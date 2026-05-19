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
        'role': role,
        'jti': str(uuid.uuid4())
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def decode_token(token):
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        from app.models import TokenBlocklist
        is_blocked = TokenBlocklist.query.filter_by(jti=payload.get('jti')).first()
        if is_blocked:
            return 'Token has been revoked. Please log in again.'
        return payload
    except jwt.ExpiredSignatureError:
        return 'Signature expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'

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

