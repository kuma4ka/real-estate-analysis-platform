from flask import Blueprint, jsonify
from app.models import User, Property
from app.core.auth import require_role

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/system', methods=['GET'])
@require_role('Admin')
def system_stats():
    """Returns sensitive system-wide metrics exclusively for Admins."""
    user_count = User.query.count()
    property_count = Property.query.count()
    active_property_count = Property.query.filter(Property.is_active).count()
    
    # Calculate role distribution safely
    roles = ['Admin', 'Analyst', 'User', 'Guest']
    role_dist = {}
    for role in roles:
        role_dist[role] = User.query.filter_by(role=role).count()
        
    return jsonify({
        "total_users": user_count,
        "total_properties": property_count,
        "active_properties": active_property_count,
        "role_distribution": role_dist
    }), 200
