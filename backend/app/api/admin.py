from flask import Blueprint, jsonify
from app.models import User, Property, UserRole
from app.core.auth import require_role
from app.core.metrics import get_uptime_seconds, get_requests_today
from app import db
from sqlalchemy import func, text

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/system', methods=['GET'])
@require_role(UserRole.ADMIN)
def system_stats():
    """Returns sensitive system-wide metrics exclusively for Admins."""
    user_count = User.query.count()
    property_count = Property.query.count()
    active_property_count = Property.query.filter(Property.is_active == True).count()

    # Single aggregated query instead of one COUNT per role
    role_rows = (
        db.session.query(User.role, func.count(User.id))
        .group_by(User.role)
        .all()
    )
    # Initialise all known roles to 0, then fill in actual counts
    role_dist = {role.value: 0 for role in UserRole}
    for role, count in role_rows:
        role_dist[role.value] = count

    # Health checks and metrics
    try:
        db.session.execute(text('SELECT 1'))
        db_status = 'Connected'
    except Exception:
        db_status = 'Error'

    return jsonify({
        "total_users": user_count,
        "total_properties": property_count,
        "active_properties": active_property_count,
        "role_distribution": role_dist,
        "server_uptime_seconds": get_uptime_seconds(),
        "total_requests_today": get_requests_today(),
        "db_status": db_status
    }), 200
