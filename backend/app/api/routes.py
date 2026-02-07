from flask import Blueprint, jsonify, request
from app import db
from app.models import Property

bp = Blueprint('api', __name__)


@bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'service': 'real-estate-backend'})


@bp.route('/properties', methods=['GET'])
def get_properties():
    properties = Property.query.order_by(Property.created_at.desc()).all()

    result = [p.to_dict() for p in properties]

    return jsonify(result)


@bp.route('/properties', methods=['POST'])
def create_property():
    data = request.get_json()

    if not data or 'source_url' not in data or 'title' not in data:
        return jsonify({'error': 'Missing required fields (title, source_url)'}), 400

    existing = Property.query.filter_by(source_url=data['source_url']).first()
    if existing:
        return jsonify({'message': 'Property already exists', 'id': existing.id}), 200

    new_property = Property(
        title=data['title'],
        source_url=data['source_url'],
        price=data.get('price'),
        currency=data.get('currency', 'USD'),
        address=data.get('address'),
        area=data.get('area'),
        rooms=data.get('rooms'),
        source_website=data.get('source_website')
    )

    try:
        db.session.add(new_property)
        db.session.commit()
        return jsonify(new_property.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500