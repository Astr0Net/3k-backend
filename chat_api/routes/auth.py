from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt,
    get_jwt_identity,
)

from ..extensions import db, bcrypt
from chat_api.models import User, TokenBlocklist

from .auth_helpers import api_ok, api_error, normalize_username
from .auth_validators import validate_username, validate_password


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = normalize_username(data.get("username"))
    password = data.get("password") or ""

    err = validate_username(username) or validate_password(password)
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
    username = normalize_username(data.get("username"))
    password = data.get("password") or ""

    if not username or not password:
        return api_error("username and password are required", 400)

    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        return api_error("invalid credentials", 401)

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