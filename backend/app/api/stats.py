from flask import jsonify
from sqlalchemy import func, case
from app.models import Property
from app.api import bp


@bp.route('/stats', methods=['GET'])
def get_stats():
    base_query = Property.query.filter(Property.is_active)
    total = base_query.count()

    avg_price_raw = base_query.with_entities(func.avg(Property.price)).scalar() or 0

    avg_area = Property.query.with_entities(
        func.avg(Property.area)
    ).filter(Property.area.isnot(None), Property.area > 0).scalar() or 0

    # Avg price per m² (global)
    avg_price_per_m2 = Property.query.with_entities(
        func.avg(Property.price / Property.area)
    ).filter(
        Property.is_active,
        Property.area.isnot(None),
        Property.area > 0,
        Property.price.isnot(None),
    ).scalar() or 0

    # By city: count + avg price + avg price/m²
    by_city = Property.query.with_entities(
        Property.city,
        func.count(Property.id).label('count'),
        func.avg(Property.price).label('avg_price'),
        func.avg(
            case(
                (Property.area > 0, Property.price / Property.area),
                else_=None
            )
        ).label('avg_price_per_m2'),
    ).filter(
        Property.city.isnot(None)
    ).group_by(Property.city).order_by(func.count(Property.id).desc()).limit(10).all()

    # By rooms: count + avg price
    by_rooms = Property.query.with_entities(
        Property.rooms,
        func.count(Property.id).label('count'),
        func.avg(Property.price).label('avg_price'),
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

    price_histogram = []
    for low, high, label in price_ranges:
        q = Property.query.filter(Property.price.isnot(None))
        if high == float('inf'):
            count = q.filter(Property.price >= low).count()
        else:
            count = q.filter(Property.price >= low, Property.price < high).count()
        price_histogram.append({'range': label, 'count': count})

    # Daily trend with % price change vs previous day
    trend_rows = Property.query.with_entities(
        func.date(Property.created_at).label('date'),
        func.count(Property.id).label('count'),
        func.avg(Property.price).label('avg_price'),
    ).group_by(func.date(Property.created_at)).order_by(
        func.date(Property.created_at)
    ).limit(30).all()

    recent_trend = []
    for i, r in enumerate(trend_rows):
        avg_p = round(r[2] or 0, 0)
        prev_p = round(trend_rows[i - 1][2] or 0, 0) if i > 0 else None
        price_change_pct = None
        if prev_p and prev_p > 0:
            price_change_pct = round((avg_p - prev_p) / prev_p * 100, 1)
        recent_trend.append({
            'date': str(r[0]),
            'count': r[1],
            'avg_price': avg_p,
            'price_change_pct': price_change_pct,
        })

    return jsonify({
        'total_listings': total,
        'avg_price_usd': round(avg_price_raw, 0),
        'avg_area': round(avg_area, 1),
        'avg_price_per_m2': round(avg_price_per_m2, 0),
        'by_city': [
            {
                'city': r[0],
                'count': r[1],
                'avg_price': round(r[2] or 0, 0),
                'avg_price_per_m2': round(r[3] or 0, 0),
            }
            for r in by_city
        ],
        'by_rooms': [
            {'rooms': r[0], 'count': r[1], 'avg_price': round(r[2] or 0, 0)}
            for r in by_rooms
        ],
        'price_histogram': price_histogram,
        'recent_trend': recent_trend,
    })
