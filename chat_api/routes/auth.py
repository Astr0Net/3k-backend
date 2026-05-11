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

from ..utils.response_utils import api_ok, api_error, normalize_username
from ..service.auth_validators import validate_username, validate_password

from flasgger import swag_from
from chat_api.docs_path import doc
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
@swag_from(doc("auth", "register.yml"))
def register():
    """
    
    """
    data = request.get_json(silent=True) or {}
    username = normalize_username(data.get("username"))
    password = data.get("password") or ""

    err = validate_username(username) or validate_password(password)
    if err:
        return api_error(err, 400)

    user = User(username=username)
    user.set_password(password)

    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return api_error("username already exists", 409)

    return api_ok(data={"user": user.to_dict()}, message="user created", http_status=201)


@auth_bp.route("/login", methods=["POST"])
@swag_from(doc("auth", "login.yml"))
def login():
    """
    
    """


    data = request.get_json(silent=True) or {}
    username = normalize_username(data.get("username"))
    password = data.get("password") or ""

    if not username or not password:
        return api_error("username and password are required", 400)

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
      return api_error("Invalid username or password", 401)


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
@swag_from(doc("auth", "refresh.yml"))
@jwt_required(refresh=True)
def refresh():
    """
    
    """

    user_id = get_jwt_identity()  # string
    new_access = create_access_token(identity=str(user_id))

    return api_ok(
        data={"access_token": new_access, "token_type": "Bearer"},
        message="token refreshed",
        http_status=200,
    )


@auth_bp.route("/logout", methods=["POST"])
@swag_from(doc("auth", "logout.yml"))
@jwt_required()
def logout():
    """
    
    """

    jwt_payload = get_jwt()
    jti = jwt_payload.get("jti")
    token_type = jwt_payload.get("type", "access")
    user_id = int(get_jwt_identity())

    if not jti:
        return api_error("invalid token payload", 401)

    db.session.add(TokenBlocklist(jti=jti, token_type=token_type, user_id=user_id))
    db.session.commit()

    return api_ok(data=None, message="logged out", http_status=200)
