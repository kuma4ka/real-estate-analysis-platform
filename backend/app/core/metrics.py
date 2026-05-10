from datetime import datetime, timezone

START_TIME = datetime.now(timezone.utc)

request_stats = {
    'date': START_TIME.date(),
    'count': 0
}

import threading

_lock = threading.Lock()

def record_request():
    today = datetime.now(timezone.utc).date()
    with _lock:
        if request_stats['date'] != today:
            request_stats['date'] = today
            request_stats['count'] = 0
        request_stats['count'] += 1

def get_uptime_seconds() -> float:
    return (datetime.now(timezone.utc) - START_TIME).total_seconds()

def get_requests_today() -> int:
    today = datetime.now(timezone.utc).date()
    with _lock:
        if request_stats['date'] != today:
            return 0
        return request_stats['count']
