from flask import jsonify, request
from sqlalchemy import desc, asc
from app.models import Property
from app.api import bp
from app.api.schemas import properties_schema, property_schema


@bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'service': 'real-estate-backend'})


@bp.route('/properties', methods=['GET'])
def get_properties():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    city = request.args.get('city')
    rooms = request.args.get('rooms', type=int)
    price_min = request.args.get('price_min', type=float)
    price_max = request.args.get('price_max', type=float)
    sort_by = request.args.get('sort', 'newest')

    query = Property.query

    if city:
        query = query.filter(Property.city.ilike(f"%{city}%"))
    if rooms:
        query = query.filter(Property.rooms == rooms)
    if price_min:
        query = query.filter(Property.price >= price_min)
    if price_max:
        query = query.filter(Property.price <= price_max)

    if sort_by == 'cheapest':
        query = query.order_by(asc(Property.price))
    elif sort_by == 'expensive':
        query = query.order_by(desc(Property.price))
    else:
        query = query.order_by(desc(Property.created_at))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'data': properties_schema.dump(pagination.items),
        'meta': {
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages,
            'total_items': pagination.total
        }
    })


@bp.route('/properties/<int:id>', methods=['GET'])
def get_property(id):
    prop = Property.query.get_or_404(id)
    return jsonify(property_schema.dump(prop))


@bp.route('/properties/map', methods=['GET'])
def get_map_properties():
    """Lightweight endpoint for map markers. Supports same filters as /properties."""
    query = Property.query.filter(
        Property.latitude.isnot(None),
        Property.longitude.isnot(None)
    )

    city = request.args.get('city')
    rooms = request.args.get('rooms', type=int)
    price_min = request.args.get('price_min', type=float)
    price_max = request.args.get('price_max', type=float)

    if city:
        query = query.filter(Property.city.ilike(f"%{city}%"))
    if rooms:
        query = query.filter(Property.rooms == rooms)
    if price_min:
        query = query.filter(Property.price >= price_min)
    if price_max:
        query = query.filter(Property.price <= price_max)

    properties = query.all()

    data = [{
        'id': p.id,
        'title': p.title,
        'price': p.price,
        'currency': p.currency,
        'address': p.address,
        'lat': p.latitude,
        'lng': p.longitude,
        'city': p.city,
        'district': p.district,
        'geocode_precision': p.geocode_precision,
        'area': p.area,
        'rooms': p.rooms,
        'floor': p.floor,
        'description': None,
        'images': p.images[:1] if p.images else [],
        'source_url': p.source_url,
        'created_at': p.created_at.isoformat() if p.created_at else None
    } for p in properties]

    return jsonify({'data': data, 'count': len(data)})