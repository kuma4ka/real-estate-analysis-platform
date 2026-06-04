import os
import jwt
import uuid
import logging
from functools import wraps
from flask import request, jsonify, g, current_app
from datetime import datetime, timedelta, timezone
from app.models import UserRole, User
from app import db, cache

logger = logging.getLogger(__name__)

_ROLE_RANK = {
    UserRole.GUEST:   0,
    UserRole.USER:    1,
    UserRole.ANALYST: 2,
    UserRole.ADMIN:   3,
}


def generate_token(user_id, role):
    expiry_hours = int(os.getenv('JWT_EXPIRY_HOURS', '24'))
    payload = {
        'exp': datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
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

    cache_key = f'blocklist_jti_{jti}'
    cached = cache.get(cache_key)

    if cached is True:
        return 'Token has been revoked. Please log in again.'

    if cached is None:
        from app.models import TokenBlocklist
        is_blocked = TokenBlocklist.query.filter_by(jti=jti).first()
        if is_blocked:
            exp = payload.get('exp', 0)
            remaining_ttl = max(1, int(exp - datetime.now(timezone.utc).timestamp()))
            cache.set(cache_key, True, timeout=remaining_ttl)
            return 'Token has been revoked. Please log in again.'
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


def require_role(required_role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not getattr(g, 'user_id', None):
                return jsonify({'message': 'Authentication required'}), 401

            user = db.session.get(User, g.user_id)
            if not user:
                return jsonify({'message': 'User not found'}), 401

            live_role = user.role
            g.role = live_role

            required_rank = _ROLE_RANK.get(required_role, 99)
            actual_rank = _ROLE_RANK.get(live_role, -1)
            if actual_rank < required_rank:
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
