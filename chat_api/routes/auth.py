import re
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt,
    get_jwt_identity,
)

from ..extensions import db, bcrypt
from chat_api.models.models import User, TokenBlocklist

auth_bp = Blueprint("auth", __name__)

USERNAME_MIN = 3
USERNAME_MAX = 32
PASSWORD_MIN = 8
PASSWORD_MAX = 128
_username_re = re.compile(r"^[a-z0-9._-]+$")


def api_ok(data=None, message="ok", http_status=200):
    payload = {"status": http_status, "message": message, "data": data}
    return jsonify(payload), http_status


def api_error(message="error", http_status=400, data=None):
    payload = {"status": http_status, "error": message, "data": data}
    return jsonify(payload), http_status


def _normalize_username(u: str) -> str:
    return (u or "").strip().lower()


def _validate_username(username: str):
    if not username:
        return "username is required"
    if not (USERNAME_MIN <= len(username) <= USERNAME_MAX):
        return f"username length must be {USERNAME_MIN}-{USERNAME_MAX}"
    if not _username_re.match(username):
        return "username contains invalid characters"
    return None


def _validate_password(password: str):
    if not password:
        return "password is required"
    if not (PASSWORD_MIN <= len(password) <= PASSWORD_MAX):
        return f"password length must be {PASSWORD_MIN}-{PASSWORD_MAX}"
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        return "password must contain at least one letter and one digit"
    return None


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = _normalize_username(data.get("username"))
    password = data.get("password") or ""

    err = _validate_username(username) or _validate_password(password)
    if err:
        return api_error(err, 400)

    hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(username=username, password=hashed_pw)

    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return api_error("username already exists", 409)

    return api_ok(data={"user": user.to_dict()}, message="user created", http_status=201)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = _normalize_username(data.get("username"))
    password = data.get("password") or ""

    if not username or not password:
        return api_error("username and password are required", 400)

    user = User.query.filter_by(username=username).first()

    if not user or not bcrypt.check_password_hash(user.password, password):
        return api_error("invalid credentials", 401)

    # ✅ identity باید string باشد تا sub در JWT استاندارد باشد
    access_token = create_access_token(identity=str(user.user_id))
    refresh_token = create_refresh_token(identity=str(user.user_id))

    return api_ok(
        data={
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
        },
        message="login successful",
        http_status=200,
    )


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()  # string
    new_access = create_access_token(identity=str(user_id))

    return api_ok(
        data={"access_token": new_access, "token_type": "Bearer"},
        message="token refreshed",
        http_status=200,
    )


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jwt_payload = get_jwt()
    jti = jwt_payload.get("jti")
    token_type = jwt_payload.get("type", "access")
    user_id = int(get_jwt_identity())

    if not jti:
        return api_error("invalid token payload", 401)

    db.session.add(TokenBlocklist(jti=jti, token_type=token_type, user_id=user_id))
    db.session.commit()

    return api_ok(data=None, message="logged out", http_status=200)


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user:
        return api_error("user not found", 404)

    return api_ok(data={"user": user.to_dict()}, message="ok", http_status=200)
