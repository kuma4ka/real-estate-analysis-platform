from datetime import datetime

START_TIME = datetime.utcnow()

request_stats = {
    'date': START_TIME.date(),
    'count': 0
}

def record_request():
    today = datetime.utcnow().date()
    if request_stats['date'] != today:
        request_stats['date'] = today
        request_stats['count'] = 0
    request_stats['count'] += 1

def get_uptime_seconds() -> float:
    return (datetime.utcnow() - START_TIME).total_seconds()

def get_requests_today() -> int:
    today = datetime.utcnow().date()
    if request_stats['date'] != today:
        return 0
    return request_stats['count']
