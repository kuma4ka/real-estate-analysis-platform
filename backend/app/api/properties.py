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
    # 1. Query Params
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    city = request.args.get('city')
    rooms = request.args.get('rooms', type=int)
    price_min = request.args.get('price_min', type=float)
    price_max = request.args.get('price_max', type=float)
    sort_by = request.args.get('sort', 'newest')

    # 2. Query Builder
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

    # 3. Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    results = pagination.items

    return jsonify({
        'data': properties_schema.dump(results),
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