from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from chat_api.extensions import db
from chat_api.models.user import User
from chat_api.utils.response_utils import api_ok, api_error

users_bp = Blueprint("users", __name__)

@users_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    """
    Get current user profile
    ---
    tags:
      - Users
    summary: Get authenticated user profile
    security:
      - BearerAuth: []
    responses:
      200:
        description: User profile retrieved successfully
      404:
        description: User not found
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user:
        return api_error("User not found", 404)

    return api_ok(data={"user": user.to_dict()}, message="ok")


@users_bp.route("/me", methods=["PATCH"])
@jwt_required()
def update_me():
    """
    Update current user profile
    ---
    tags:
      - Users
    summary: Update authenticated user profile
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            first_name:
              type: string
            last_name:
              type: string
            phone:
              type: string
            avatar:
              type: string
            bio:
              type: string
    responses:
      200:
        description: Profile updated successfully
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user:
        return api_error("User not found", 404)

    data = request.get_json() or {}
    new_username = data.get("username")

    if not new_username:
        return api_error("Username is required", 400)

    # جلوگیری از تکراری بودن username
    existing_user = User.query.filter_by(username=new_username).first()
    if existing_user and existing_user.user_id != user.user_id:
        return api_error("Username already taken", 400)

    user.username = new_username

    try:
        db.session.commit()
        return api_ok(
            data={"user": user.to_dict()},
            message="Profile updated successfully"
        )
    except Exception:
        db.session.rollback()
        return api_error("Update failed", 500)



@users_bp.route("/me/password", methods=["PATCH"])
@jwt_required()
def change_password():
    """
    Change user password
    ---
    tags:
      - Users
    summary: Change authenticated user password
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - current_password
            - new_password
          properties:
            current_password:
              type: string
            new_password:
              type: string
    responses:
      200:
        description: Password changed successfully
      401:
        description: Current password incorrect
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user:
        return api_error("User not found", 404)

    data = request.get_json() or {}
    current_password = data.get("current_password")
    new_password = data.get("new_password")

    if not current_password or not new_password:
        return api_error("Current and new password are required", 400)

    # استفاده از متد جدید مدل برای چک کردن پسورد
    if not user.check_password(current_password):
        return api_error("Current password is incorrect", 401)

    # استفاده از متد جدید مدل برای ست کردن پسورد جدید (خودش هش می‌کند)
    user.set_password(new_password)

    try:
        db.session.commit()
        return api_ok(message="Password changed successfully")
    except Exception as e:
        db.session.rollback()
        return api_error("Failed to update password", 500)


@users_bp.route("/me", methods=["DELETE"])
@jwt_required()
def delete_account():
    """
    Delete user account and all data
    ---
    tags:
      - Users
    summary: Delete authenticated user account (Cascade delete enabled)
    security:
      - BearerAuth: []
    responses:
      200:
        description: Account and all associated data deleted successfully
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user:
        return api_error("User not found", 404)

    try:
        # چون در مدل User رابطه chats را با cascade="all, delete-orphan" تعریف کردی،
        # حذف کردن user به طور خودکار تمام چت‌ها و پیام‌هایش را هم پاک می‌کند.
        db.session.delete(user)
        db.session.commit()
        return api_ok(message="Account and all related history deleted successfully")
    except Exception as e:
        db.session.rollback()
        return api_error(f"Error deleting account: {str(e)}", 500)
