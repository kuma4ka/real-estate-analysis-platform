import re
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, g
from app.models import User
from app import db, limiter
from app.core.auth import generate_token, require_auth
from marshmallow import Schema, fields, ValidationError

auth_bp = Blueprint('auth', __name__)

def validate_password(p):
    if len(p) < 8:
        raise ValidationError("Password must be at least 8 characters long")
    if not re.search(r"[A-Z]", p):
        raise ValidationError("Password must contain at least one uppercase letter")
    if not re.search(r"\d", p):
        raise ValidationError("Password must contain at least one digit")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", p):
        raise ValidationError("Password must contain at least one special character")
    return True

class RegisterSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate_password)

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True)

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per day")
def register():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No input data provided"}), 400

    try:
        validated_data = RegisterSchema().load(data)
    except ValidationError as err:
        return jsonify({"message": "Validation error", "errors": err.messages}), 400

    if User.query.filter_by(email=validated_data['email']).first():
        return jsonify({"message": "User with this email already exists"}), 409

    new_user = User(email=validated_data['email'])
    new_user.set_password(validated_data['password'])

    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Database error"}), 500

    token = generate_token(new_user.id, new_user.role)
    return jsonify({
        "message": "User registered successfully",
        "token": token,
        "user": new_user.to_dict()
    }), 201

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No input data provided"}), 400

    try:
        validated_data = LoginSchema().load(data)
    except ValidationError as err:
        return jsonify({"message": "Validation error", "errors": err.messages}), 400

    user = User.query.filter_by(email=validated_data['email']).first()

    if user:
        if user.locked_until:
            now = datetime.now(timezone.utc)
            locked_until = user.locked_until
            # SQLite stores naive datetimes; make comparison timezone-safe
            if locked_until.tzinfo is None:
                now = now.replace(tzinfo=None)
            if locked_until > now:
                return jsonify({"message": "Account temporarily locked. Please try again later."}), 429

        if user.check_password(validated_data['password']):
            token = generate_token(user.id, user.role)
            user.last_login = datetime.now(timezone.utc)
            user.failed_login_attempts = 0
            user.locked_until = None
            db.session.commit()
            return jsonify({
                "token": token,
                "user": user.to_dict()
            }), 200
        else:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
            db.session.commit()

    return jsonify({"message": "Invalid email or password"}), 401

@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_me():
    user = db.session.get(User, g.user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    return jsonify(user.to_dict()), 200

class PasswordChangeSchema(Schema):
    old_password = fields.String(required=True)
    new_password = fields.String(required=True, validate=validate_password)

@auth_bp.route('/me/password', methods=['PUT'])
@require_auth
@limiter.limit("5 per hour")
def change_password():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No input data provided"}), 400

    try:
        validated_data = PasswordChangeSchema().load(data)
    except ValidationError as err:
        return jsonify({"message": "Validation error", "errors": err.messages}), 400

    user = db.session.get(User, g.user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    if not user.check_password(validated_data['old_password']):
        return jsonify({"message": "Incorrect old password"}), 400

    user.set_password(validated_data['new_password'])
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Database error"}), 500

    return jsonify({"message": "Password updated successfully"}), 200
