import csv
import io
from datetime import date, timedelta
from flask import jsonify, Response, request
from sqlalchemy import func, case
from app.models import Property, UserRole
from app.api import bp
from app.core.auth import require_role
from app import cache
from app.services.cities import CITIES


@cache.cached(timeout=600, key_prefix='_available_cities')
def _get_available_cities() -> list[str]:
    """Returns the top-20 cities by listing count. Cached separately so
    every per-city forecast entry does not redundantly store this list."""
    rows = (
        Property.query
        .with_entities(Property.city)
        .filter(Property.city.isnot(None))
        .group_by(Property.city)
        .order_by(func.count(Property.id).desc())
        .limit(20)
        .all()
    )
    return [r[0] for r in rows]

@cache.cached(timeout=600, key_prefix='_compute_stats')
def _compute_stats():
    base_query = Property.query.filter(Property.is_active == True)
    total = base_query.count()

    avg_price_raw = base_query.with_entities(func.avg(Property.price)).scalar() or 0

    avg_area = Property.query.with_entities(
        func.avg(Property.area)
    ).filter(
        Property.is_active == True,
        Property.area.isnot(None),
        Property.area > 0,
    ).scalar() or 0

    # Avg price per m² (global)
    avg_price_per_m2 = Property.query.with_entities(
        func.avg(Property.price / Property.area)
    ).filter(
        Property.is_active == True,
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
        Property.is_active == True,
        Property.city.isnot(None)
    ).group_by(Property.city).order_by(func.count(Property.id).desc()).limit(10).all()

    # By rooms: count + avg price
    by_rooms = Property.query.with_entities(
        Property.rooms,
        func.count(Property.id).label('count'),
        func.avg(Property.price).label('avg_price'),
    ).filter(
        Property.is_active == True,
        Property.rooms.isnot(None),
    ).group_by(Property.rooms).order_by(Property.rooms).all()

    _PRICE_BUCKET_ORDER = ['<$10k', '$10-25k', '$25-50k', '$50-100k', '$100-250k', '$250k+']

    _price_bucket = case(
        (Property.price < 10_000, '<$10k'),
        (Property.price < 25_000, '$10-25k'),
        (Property.price < 50_000, '$25-50k'),
        (Property.price < 100_000, '$50-100k'),
        (Property.price < 250_000, '$100-250k'),
        else_='$250k+'
    )
    _histogram_rows = (
        Property.query
        .with_entities(_price_bucket.label('range'), func.count().label('count'))
        .filter(Property.is_active == True, Property.price.isnot(None))
        .group_by(_price_bucket)
        .all()
    )
    _counts = {r[0]: r[1] for r in _histogram_rows}
    price_histogram = [
        {'range': label, 'count': _counts.get(label, 0)}
        for label in _PRICE_BUCKET_ORDER
    ]

    # Daily trend with % price change vs previous day
    trend_rows = Property.query.with_entities(
        func.date(Property.created_at).label('date'),
        func.count(Property.id).label('count'),
        func.avg(Property.price).label('avg_price'),
    ).filter(
        Property.is_active == True,
    ).group_by(func.date(Property.created_at)).order_by(
        func.date(Property.created_at).desc()
    ).limit(30).all()
    trend_rows = list(reversed(trend_rows))

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
@require_role(UserRole.ANALYST)
def get_stats():
    return jsonify(_compute_stats())


@cache.memoize(timeout=600)
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

    # Fetch available cities from the shared cached function.
    available_cities = _get_available_cities()

    if len(rows) < 3:
        return {
            'available_cities': available_cities,
            'r_squared': 0.0,
            'slope_per_day': 0.0,
            'historical': [],
            'forecast': [],
            'error': 'Not enough historical data for a forecast (need \u2265 3 days)',
        }

    # Convert dates to integer offsets (day 0 = first data point)
    def to_date(val):
        if isinstance(val, date):
            return val
        if hasattr(val, 'date'):
            return val.date()
        return date.fromisoformat(str(val))

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
    # Clamp the forecast floor at 50% of the last known price.
    last_actual_price = float(ys[-1]) if len(ys) > 0 else 0.0
    price_floor = max(0.0, last_actual_price * 0.5)
    forecast = []
    for i in range(1, 31):
        future_x = last_x + i
        future_date = last_date + timedelta(days=i)
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
        'available_cities': available_cities,
        'r_squared': r_squared,
        'slope_per_day': round(slope, 2),
        'historical': historical,
        'forecast': forecast,
    }

@bp.route('/stats/forecast', methods=['GET'])
@require_role(UserRole.ANALYST)
def get_price_forecast():
    """
    Linear-regression price forecast for the next 30 days.

    Query params:
      city (optional) – filter to a specific city; omit for global data.
    """
    city_filter = request.args.get('city', '').strip() or None

    # Validate city against the known set to prevent unbounded cache key growth.
    # An attacker could otherwise exhaust the cache store by sending arbitrary
    # ?city= values, each creating a new memoize entry.
    if city_filter and city_filter not in CITIES:
        return jsonify({'error': f"Unknown city: '{city_filter}'"}), 400

    res = _compute_price_forecast(city_filter)
    if res.get('error_override'):
        return jsonify({'error': 'Forecast service unavailable'}), res['status']

    return jsonify(res)



@bp.route('/stats/export', methods=['GET'])
@require_role(UserRole.ANALYST)
def export_stats_csv():
    """Stream active properties as a CSV without loading all rows into RAM."""
    CHUNK_SIZE = 500

    def _csv_safe(value):
        s = str(value) if value is not None else ''
        if s and s[0] in ('=', '+', '-', '@', '\t', '\r'):
            return "'" + s
        return s

    def generate():
        header = ['id', 'title', 'price', 'currency', 'city', 'district',
                  'area', 'rooms', 'floor', 'address', 'created_at']
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(header)
        yield buf.getvalue()

        query = (
            Property.query
            .filter(Property.is_active == True)
            .order_by(Property.created_at.desc())
            .yield_per(CHUNK_SIZE)
        )
        for p in query:
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow([
                p.id, _csv_safe(p.title), p.price, p.currency,
                _csv_safe(p.city), _csv_safe(p.district),
                p.area, p.rooms, p.floor, _csv_safe(p.address),
                p.created_at.isoformat() if p.created_at else None,
            ])
            yield buf.getvalue()

    return Response(
        generate(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=market_export.csv'},
    )