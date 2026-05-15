from datetime import datetime, timezone

START_TIME = datetime.now(timezone.utc)


def record_request():
    from app import cache
    today = datetime.now(timezone.utc).date().isoformat()
    key = f'req_count_{today}'
    count = cache.get(key) or 0
    cache.set(key, count + 1, timeout=86_400)


def get_uptime_seconds() -> float:
    return (datetime.now(timezone.utc) - START_TIME).total_seconds()


def get_requests_today() -> int:
    from app import cache
    today = datetime.now(timezone.utc).date().isoformat()
    return cache.get(f'req_count_{today}') or 0
