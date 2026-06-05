import os
from flask import jsonify, request, abort, g
from sqlalchemy import desc, asc, or_
from app.models import Property
from app.api import bp
from app import db
from app.api.schemas import properties_schema, property_schema
from app.core.auth import optional_auth
from app.services.cities import CITIES

MAX_MAP_PINS = int(os.getenv('MAX_MAP_PINS', '5000'))
MAX_PAGE_SIZE = 100


def _resolve_city_alias(name):
    """Resolve a city alias (e.g. 'Kyiv') to the canonical Ukrainian name ('Київ')."""
    if not name:
        return name
    lower = name.strip().lower()
    for canonical, info in CITIES.items():
        if canonical.lower() == lower:
            return canonical
        for alias in info.get('aliases', []):
            if alias.lower() == lower:
                return canonical
    return name


def _is_authenticated() -> bool:
    return getattr(g, 'user_id', None) is not None


@bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'service': 'real-estate-backend'})


@bp.route('/properties', methods=['GET'])
@optional_auth
def get_properties():
    page = max(1, request.args.get('page', 1, type=int))
    per_page = min(request.args.get('per_page', 20, type=int), MAX_PAGE_SIZE)
    city = request.args.get('city')
    rooms = request.args.get('rooms', type=int)
    price_min = request.args.get('price_min', type=float)
    price_max = request.args.get('price_max', type=float)
    sort_by = request.args.get('sort', 'newest')
    search = request.args.get('search', type=str)

    if price_min is not None and price_min < 0:
        return jsonify({"message": "price_min cannot be negative"}), 400
    if price_max is not None and price_max < 0:
        return jsonify({"message": "price_max cannot be negative"}), 400

    query = Property.query.filter(Property.is_active == True)

    if search:
        if len(search) > 200:
            return jsonify({"message": "search parameter too long (max 200 chars)"}), 400
        term = f"%{search}%"
        query = query.filter(
            or_(
                Property.title.ilike(term),
                Property.address.ilike(term)
            )
        )

    if city:
        if len(city) > 100:
            return jsonify({"message": "city parameter too long"}), 400
        resolved = _resolve_city_alias(city)
        query = query.filter(Property.city.ilike(f"{resolved}%"))
    if rooms is not None:
        query = query.filter(Property.rooms == rooms)
    if price_min is not None:
        query = query.filter(Property.price >= price_min)
    if price_max is not None:
        query = query.filter(Property.price <= price_max)

    if sort_by == 'cheapest':
        query = query.order_by(asc(Property.price))
    elif sort_by == 'expensive':
        query = query.order_by(desc(Property.price))
    else:
        query = query.order_by(desc(Property.created_at))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    data = properties_schema.dump(pagination.items)

    if not _is_authenticated():
        for item in data:
            item['source_url'] = None

    return jsonify({
        'data': data,
        'meta': {
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages,
            'total_items': pagination.total
        }
    })


@bp.route('/properties/<int:id>', methods=['GET'])
@optional_auth
def get_property(id):
    prop = db.session.get(Property, id)
    if prop is None:
        abort(404)
    data = property_schema.dump(prop)

    if not _is_authenticated():
        data['source_url'] = None

    return jsonify(data)


@bp.route('/properties/map', methods=['GET'])
@optional_auth
def get_map_properties():
    """Lightweight endpoint for map markers. Supports same filters as /properties."""
    query = Property.query.filter(
        Property.latitude.isnot(None),
        Property.longitude.isnot(None),
        Property.is_active == True
    )

    city = request.args.get('city')
    rooms = request.args.get('rooms', type=int)
    price_min = request.args.get('price_min', type=float)
    price_max = request.args.get('price_max', type=float)

    if city:
        if len(city) > 100:
            return jsonify({"message": "city parameter too long"}), 400
        resolved = _resolve_city_alias(city)
        query = query.filter(Property.city.ilike(f"{resolved}%"))
    if rooms is not None:
        query = query.filter(Property.rooms == rooms)
    if price_min is not None:
        if price_min < 0:
            return jsonify({"message": "price_min cannot be negative"}), 400
        query = query.filter(Property.price >= price_min)
    if price_max is not None:
        if price_max < 0:
            return jsonify({"message": "price_max cannot be negative"}), 400
        query = query.filter(Property.price <= price_max)

    properties = (
        query
        .with_entities(
            Property.id, Property.title, Property.price, Property.currency,
            Property.address, Property.latitude, Property.longitude,
            Property.city, Property.district, Property.geocode_precision,
            Property.area, Property.rooms, Property.floor,
            Property.images, Property.source_url, Property.created_at,
        )
        .limit(MAX_MAP_PINS)
        .all()
    )

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
        'images': (p.images or [])[:1],
        'source_url': p.source_url,
        'created_at': p.created_at.isoformat() if p.created_at else None
    } for p in properties]

    if not _is_authenticated():
        for item in data:
            item['source_url'] = None

    return jsonify({'data': data, 'count': len(data)})