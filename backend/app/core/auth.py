import jwt
import uuid
from functools import wraps
from flask import request, jsonify, g, current_app
from datetime import datetime, timedelta, timezone
from app.models import UserRole

def generate_token(user_id, role):
    payload = {
        'exp': datetime.now(timezone.utc) + timedelta(days=1),
        'iat': datetime.now(timezone.utc),
        'sub': str(user_id),
        'role': role.value if hasattr(role, 'value') else role,
        'jti': str(uuid.uuid4())
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def decode_token(token):
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return 'Signature expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'

    jti = payload.get('jti')
    if not jti:
        return 'Invalid token. Please log in again.'

    # --- Redis-first blocklist check ---
    # Check the cache before touching the database. Positive hits (revoked
    # tokens) are stored with a TTL equal to the token's remaining lifetime so
    # the entry auto-cleans up when the JWT would have expired anyway.
    from app import cache
    cache_key = f'blocklist_jti_{jti}'
    cached = cache.get(cache_key)

    if cached is True:
        # Fast path: cache says this JTI is revoked — no DB query needed.
        return 'Token has been revoked. Please log in again.'

    if cached is None:
        # Cache miss — check the database and populate the cache.
        from app.models import TokenBlocklist
        is_blocked = TokenBlocklist.query.filter_by(jti=jti).first()
        if is_blocked:
            # Calculate remaining TTL from the token's exp claim (in seconds).
            exp = payload.get('exp', 0)
            remaining_ttl = max(1, int(exp - datetime.now(timezone.utc).timestamp()))
            cache.set(cache_key, True, timeout=remaining_ttl)
            return 'Token has been revoked. Please log in again.'
        # Token is valid — cache a negative result briefly to reduce DB load
        # during burst traffic. 60 s is short enough to handle edge cases.
        cache.set(cache_key, False, timeout=60)

    return payload


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                auth_token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Bearer token malformed'}), 401
        else:
            auth_token = ''

        if auth_token:
            resp = decode_token(auth_token)
            if not isinstance(resp, str):
                g.user_id = int(resp['sub'])
                g.role = resp['role']
                g.jti = resp.get('jti')
                return f(*args, **kwargs)
            return jsonify({'message': resp}), 401
        
        return jsonify({'message': 'Provide a valid auth token'}), 401
    return decorated

def require_role(role_name):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not getattr(g, 'user_id', None):
                return jsonify({'message': 'Authentication required'}), 401

            from app.models import User
            from app import db
            user = db.session.get(User, g.user_id)
            if not user:
                return jsonify({'message': 'User not found'}), 401

            live_role = user.role
            g.role = live_role

            ROLE_HIERARCHY = {
                UserRole.GUEST:   {UserRole.GUEST, UserRole.USER, UserRole.ANALYST, UserRole.ADMIN},
                UserRole.USER:    {UserRole.USER, UserRole.ANALYST, UserRole.ADMIN},
                UserRole.ANALYST: {UserRole.ANALYST, UserRole.ADMIN},
                UserRole.ADMIN:   {UserRole.ADMIN},
            }

            allowed = ROLE_HIERARCHY.get(role_name, {role_name})
            if live_role not in allowed:
                return jsonify({'message': 'Insufficient permissions'}), 403

            return f(*args, **kwargs)
        return require_auth(decorated)
    return decorator


def optional_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
            payload = decode_token(token)
            if isinstance(payload, dict):
                g.user_id = int(payload['sub'])
                g.role = payload['role']
                g.jti = payload.get('jti')
        return f(*args, **kwargs)
    return decorated

