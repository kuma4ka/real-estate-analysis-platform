from flask import Blueprint, jsonify
from app.models import User, Property, UserRole
from app.core.auth import require_role
from app.core.metrics import get_uptime_seconds, get_requests_today
from app import db
from sqlalchemy import text

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/system', methods=['GET'])
@require_role(UserRole.ADMIN)
def system_stats():
    """Returns sensitive system-wide metrics exclusively for Admins."""
    user_count = User.query.count()
    property_count = Property.query.count()
    active_property_count = Property.query.filter(Property.is_active == True).count()

    roles = [UserRole.ADMIN, UserRole.ANALYST, UserRole.USER, UserRole.GUEST]
    role_dist = {}
    for role in roles:
        role_dist[role] = User.query.filter_by(role=role).count()
        
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
