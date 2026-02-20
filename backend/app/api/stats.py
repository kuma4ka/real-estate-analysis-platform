from flask import jsonify
from sqlalchemy import func, case
from app.models import Property
from app.api import bp


@bp.route('/stats', methods=['GET'])
def get_stats():
    base_query = Property.query.filter(Property.is_active)
    total = base_query.count()

    avg_price_raw = base_query.with_entities(
        func.avg(
            case(
                (Property.currency == 'UAH', Property.price / 41.0),
                else_=Property.price
            )
        )
    ).scalar() or 0

    avg_area = Property.query.with_entities(
        func.avg(Property.area)
    ).filter(Property.area.isnot(None), Property.area > 0).scalar() or 0

    by_city = Property.query.with_entities(
        Property.city,
        func.count(Property.id).label('count'),
        func.avg(
            case(
                (Property.currency == 'UAH', Property.price / 41.0),
                else_=Property.price
            )
        ).label('avg_price')
    ).filter(
        Property.city.isnot(None)
    ).group_by(Property.city).order_by(func.count(Property.id).desc()).limit(10).all()

    by_rooms = Property.query.with_entities(
        Property.rooms,
        func.count(Property.id).label('count'),
        func.avg(
            case(
                (Property.currency == 'UAH', Property.price / 41.0),
                else_=Property.price
            )
        ).label('avg_price')
    ).filter(
        Property.rooms.isnot(None)
    ).group_by(Property.rooms).order_by(Property.rooms).all()

    price_ranges = [
        (0, 10000, '<$10k'),
        (10000, 25000, '$10-25k'),
        (25000, 50000, '$25-50k'),
        (50000, 100000, '$50-100k'),
        (100000, 250000, '$100-250k'),
        (250000, float('inf'), '$250k+'),
    ]

    price_usd_expr = case(
        (Property.currency == 'UAH', Property.price / 41.0),
        else_=Property.price
    )

    price_histogram = []
    for low, high, label in price_ranges:
        q = Property.query.filter(Property.price.isnot(None))
        if high == float('inf'):
            count = q.filter(price_usd_expr >= low).count()
        else:
            count = q.filter(price_usd_expr >= low, price_usd_expr < high).count()
        price_histogram.append({'range': label, 'count': count})

    recent_trend = Property.query.with_entities(
        func.date(Property.created_at).label('date'),
        func.count(Property.id).label('count'),
        func.avg(
            case(
                (Property.currency == 'UAH', Property.price / 41.0),
                else_=Property.price
            )
        ).label('avg_price')
    ).group_by(func.date(Property.created_at)).order_by(
        func.date(Property.created_at)
    ).limit(30).all()

    return jsonify({
        'total_listings': total,
        'avg_price_usd': round(avg_price_raw, 0),
        'avg_area': round(avg_area, 1),
        'by_city': [{'city': r[0], 'count': r[1], 'avg_price': round(r[2] or 0, 0)} for r in by_city],
        'by_rooms': [{'rooms': r[0], 'count': r[1], 'avg_price': round(r[2] or 0, 0)} for r in by_rooms],
        'price_histogram': price_histogram,
        'recent_trend': [{'date': str(r[0]), 'count': r[1], 'avg_price': round(r[2] or 0, 0)} for r in recent_trend],
    })
