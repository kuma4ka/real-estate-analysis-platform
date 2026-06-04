from datetime import datetime, timezone
from app import cache

START_TIME = datetime.now(timezone.utc)

_REQ_KEY_PREFIX = 'req_count_'


def _today_key() -> str:
    return _REQ_KEY_PREFIX + datetime.now(timezone.utc).date().isoformat()


def record_request():
    key = _today_key()
    try:
        cache.inc(key, delta=1)
    except Exception:
        count = cache.get(key) or 0
        cache.set(key, count + 1, timeout=86_400)


def get_uptime_seconds() -> float:
    return (datetime.now(timezone.utc) - START_TIME).total_seconds()


def get_requests_today() -> int:
    return cache.get(_today_key()) or 0
