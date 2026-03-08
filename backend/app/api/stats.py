from flask import jsonify
from sqlalchemy import func, case
from app.models import Property
from app.api import bp
from app.core.auth import require_role
import datetime
from cachetools import cached, TTLCache


@cached(cache=TTLCache(maxsize=4, ttl=600))
def _compute_stats():
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
            'month': str(r[0]),
            'count': r[1],
            'avg_price': avg_p,
            'price_change_pct': price_change_pct,
        })

    return {
        'total_active': total,
        'avg_price': round(avg_price_raw, 0),
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
        'by_price_ranges': price_histogram,
        'recent_trend': recent_trend,
    }

@bp.route('/stats', methods=['GET'])
@require_role('Analyst')
def get_stats():
    return jsonify(_compute_stats())


@cached(cache=TTLCache(maxsize=32, ttl=600))
def _compute_price_forecast(city_filter):
    try:
        import numpy as np
    except ImportError:
        return {'error_override': True, 'msg': 'numpy not available on this server', 'status': 500}

    # Build the historical rows query, optionally filtered by city
    base = Property.query.with_entities(
        func.date(Property.created_at).label('date'),
        func.avg(Property.price).label('avg_price'),
    ).filter(
        Property.price.isnot(None),
        Property.created_at.isnot(None),
    )
    if city_filter:
        base = base.filter(Property.city == city_filter)

    rows = base.group_by(func.date(Property.created_at)).order_by(
        func.date(Property.created_at)
    ).all()

    # Fetch available cities for the dropdown (always global)
    city_rows = (
        Property.query
        .with_entities(Property.city)
        .filter(Property.city.isnot(None))
        .group_by(Property.city)
        .order_by(func.count(Property.id).desc())
        .limit(20)
        .all()
    )
    available_cities = [r[0] for r in city_rows]

    if len(rows) < 3:
        return {
            'city': city_filter,
            'available_cities': available_cities,
            'r_squared': 0.0,
            'slope_per_day': 0.0,
            'historical': [],
            'forecast': [],
            'error': 'Not enough historical data for a forecast (need \u2265 3 days)',
        }

    # Convert dates to integer offsets (day 0 = first data point)
    def to_date(val):
        if isinstance(val, datetime.date):
            return val
        if hasattr(val, 'date'):
            return val.date()
        return datetime.date.fromisoformat(str(val))

    base_date = to_date(rows[0][0])
    xs = np.array([(to_date(r[0]) - base_date).days for r in rows], dtype=float)
    ys = np.array([float(r[1] or 0) for r in rows], dtype=float)

    # Least-squares linear fit
    coeffs = np.polyfit(xs, ys, 1)
    slope = float(coeffs[0])

    predicted_hist = np.polyval(coeffs, xs)
    residuals = ys - predicted_hist
    ss_res = float(np.sum(residuals ** 2))
    ss_tot = float(np.sum((ys - ys.mean()) ** 2))
    r_squared = round(1 - ss_res / ss_tot, 4) if ss_tot > 0 else 0.0
    sigma = float(np.std(residuals))

    # Forecast: next 30 days after the last data point
    last_x = int(xs[-1])
    last_date = to_date(rows[-1][0])
    
    # Real estate prices cannot realistically drop to $0. 
    # We establish a maximum naive drop constraint: 50% of the last known price.
    last_actual_price = float(ys[-1]) if len(ys) > 0 else 0.0
    price_floor = max(0.0, last_actual_price * 0.5)

    forecast = []
    for i in range(1, 31):
        future_x = last_x + i
        future_date = last_date + datetime.timedelta(days=i)
        raw_price = float(np.polyval(coeffs, future_x))
        clamped_price = max(price_floor, raw_price)
        
        forecast.append({
            'date': future_date.isoformat(),
            'predicted_price': round(clamped_price, 0),
            'lower': round(max(price_floor * 0.8, clamped_price - sigma), 0),
            'upper': round(clamped_price + sigma, 0),
        })

    historical = []
    for r in rows:
        historical.append({
            'date': to_date(r[0]).isoformat(),
            'avg_price': round(float(r[1] or 0), 0)
        })

    return {
        'city': city_filter,
        'available_cities': available_cities,
        'r_squared': r_squared,
        'slope_per_day': round(slope, 2),
        'historical': historical,
        'forecast': forecast,
    }

@bp.route('/stats/forecast', methods=['GET'])
@require_role('Analyst')
def get_price_forecast():
    """
    Linear-regression price forecast for the next 30 days.

    Query params:
      city (optional) – filter to a specific city; omit for global data.
    """
    from flask import request as flask_request
    
    city_filter = flask_request.args.get('city', '').strip() or None
    
    res = _compute_price_forecast(city_filter)
    if res.get('error_override'):
        return jsonify({'error': res['msg']}), res['status']
        
    return jsonify(res)

