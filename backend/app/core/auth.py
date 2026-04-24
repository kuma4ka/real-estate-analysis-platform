import jwt
import uuid
from functools import wraps
from flask import request, jsonify, g, current_app
from datetime import datetime, timedelta, timezone

def generate_token(user_id, role):
    payload = {
        'exp': datetime.now(timezone.utc) + timedelta(days=1),
        'iat': datetime.now(timezone.utc),
        'sub': user_id,
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
                g.user_id = resp['sub']
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
            if not getattr(g, 'role', None):
                return jsonify({'message': 'Role missing or token not processed'}), 401
            # Basic hierarchy checking or exact match
            if g.role == 'Admin':
                pass # Admin can do everything
            elif g.role == role_name:
                pass # Authorized
            elif role_name == 'User' and g.role in ['User', 'Analyst', 'Admin']:
                pass # Analysts/Admins also count as Users
            else:
                return jsonify({'message': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return require_auth(decorated)
    return decorator
