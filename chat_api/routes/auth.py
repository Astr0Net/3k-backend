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


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user
    ---
    tags:
      - Auth
    summary: Create a new user account
    description: >
      Creates a new user using a username and password.
      The username is normalized before validation and saving.
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              example: mohammad
            password:
              type: string
              example: StrongPass123
    responses:
      201:
        description: User created successfully
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 201
            message:
              type: string
              example: user created
            data:
              type: object
              properties:
                user:
                  type: object
      400:
        description: Invalid username or password
        schema:
          type: object
          properties:
            status:
              type: integer
            error:
              type: string
              example: username is invalid
            data:
              type: object
              nullable: true
      409:
        description: Username already exists
        schema:
          type: object
          properties:
            status:
              type: integer
            error:
              type: string
              example: username already exists
            data:
              type: object
              nullable: true
    """
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
    """
    Login user
    ---
    tags:
      - Auth
    summary: Authenticate user and return JWT tokens
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              example: johndoe
            password:
              type: string
              example: strongPassword123
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            status:
              type: integer
            message:
              type: string
              example: login successful
            data:
              type: object
              properties:
                user:
                  type: object
                access_token:
                  type: string
                refresh_token:
                  type: string
                token_type:
                  type: string
                  example: Bearer
      400:
        description: Username and password are required
      401:
        description: Invalid credentials
    """


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
    """
    Refresh access token
    ---
    tags:
      - Auth
    summary: Generate new access token using refresh token
    security:
      - BearerAuth: []
    responses:
      200:
        description: Token refreshed
        schema:
          type: object
          properties:
            status:
              type: integer
            message:
              type: string
              example: token refreshed
            data:
              type: object
              properties:
                access_token:
                  type: string
                token_type:
                  type: string
                  example: Bearer
      401:
        description: Invalid or missing refresh token
    """

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
    """
    Logout user
    ---
    tags:
      - Auth
    summary: Invalidate the current JWT token
    security:
      - BearerAuth: []
    responses:
      200:
        description: Logged out successfully
        schema:
          type: object
          properties:
            status:
              type: integer
            message:
              type: string
              example: logged out
            data:
              type: object
              nullable: true
      401:
        description: Invalid token payload
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


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """
    Get current user
    ---
    tags:
      - Auth
    summary: Get authenticated user information
    security:
      - BearerAuth: []
    responses:
      200:
        description: User information retrieved
        schema:
          type: object
          properties:
            status:
              type: integer
            message:
              type: string
              example: ok
            data:
              type: object
              properties:
                user:
                  type: object
      404:
        description: User not found
    """

    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user:
        return api_error("user not found", 404)

    return api_ok(data={"user": user.to_dict()}, message="ok", http_status=200)