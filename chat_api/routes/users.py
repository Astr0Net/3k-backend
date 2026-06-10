"""
User Profile Routes
====================

This module provides endpoints for managing the authenticated user's profile.

Available operations:

- Retrieve current user profile
- Update username, email, phone number
- Change password
- Delete account (cascade delete enabled)

All endpoints require JWT authentication.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from chat_api.extensions import db
from chat_api.models.user import User
from chat_api.utils.response_utils import api_ok, api_error
from chat_api.service.auth_validators import (
    validate_username,
    validate_email,
    validate_phone_number,
    validate_password,
)
from flasgger import swag_from
from chat_api.service.docs_path import doc
users_bp = Blueprint("users", __name__)


# ============================================================
#                       GET PROFILE
# ============================================================

@users_bp.route("/me", methods=["GET"])
@swag_from(doc("user", "get_me.yml"))
@jwt_required()
def get_me():
    """
    
    """

    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)

    if not user:
        return api_error("User not found", 404)

    return api_ok(
        data={"user": user.to_dict()},
        message="ok"
    )


# ============================================================
#                       UPDATE PROFILE
# ============================================================

@users_bp.route("/me", methods=["PATCH"])
@swag_from(doc("user", "update_me.yml"))
@jwt_required()
def update_me():
    """
    
    """

    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)

    if not user:
        return api_error("User not found", 404)

    data = request.get_json(silent=True) or {}

    new_username = data.get("username")
    new_email = data.get("email")
    new_phone = data.get("phone_number")

    # --------------------------------------------------------
    # Username Update
    # --------------------------------------------------------
    if new_username:
        err = validate_username(new_username)
        if err:
            return api_error(err, 400)

        existing_user = User.query.filter_by(username=new_username).first()
        if existing_user and existing_user.user_id != user.user_id:
            return api_error("Username already taken", 409)

        user.username = new_username

    # --------------------------------------------------------
    # Email Update
    # --------------------------------------------------------
    if new_email:
        err = validate_email(new_email)
        if err:
            return api_error(err, 400)

        existing_email = User.query.filter_by(email=new_email).first()
        if existing_email and existing_email.user_id != user.user_id:
            return api_error("Email already exists", 409)

        user.email = new_email

    # --------------------------------------------------------
    # Phone Update
    # --------------------------------------------------------
    if new_phone:
        err = validate_phone_number(new_phone)
        if err:
            return api_error(err, 400)

        existing_phone = User.query.filter_by(phone_number=new_phone).first()
        if existing_phone and existing_phone.user_id != user.user_id:
            return api_error("Phone number already exists", 409)

        user.phone_number = new_phone

    try:
        db.session.commit()
        return api_ok(
            data={"user": user.to_dict()},
            message="Profile updated successfully"
        )
    except IntegrityError:
        db.session.rollback()
        return api_error("Duplicate data detected", 409)
    except Exception:
        db.session.rollback()
        return api_error("Update failed", 500)


# ============================================================
#                       CHANGE PASSWORD
# ============================================================

@users_bp.route("/me/password", methods=["PATCH"])
@swag_from(doc("user", "change_password.yml"))
@jwt_required()
def change_password():
    """
    
    """

    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)

    if not user:
        return api_error("User not found", 404)

    data = request.get_json(silent=True) or {}
    current_password = data.get("current_password")
    new_password = data.get("new_password")

    if not current_password or not new_password:
        return api_error("Current and new password are required", 400)

    if not user.check_password(current_password):
        return api_error("Current password is incorrect", 401)

    # Validate new password
    err = validate_password(new_password)
    if err:
        return api_error(err, 400)

    user.set_password(new_password)

    try:
        db.session.commit()
        return api_ok(message="Password changed successfully")
    except Exception:
        db.session.rollback()
        return api_error("Failed to update password", 500)


# ============================================================
#                       DELETE ACCOUNT
# ============================================================

@users_bp.route("/me", methods=["DELETE"])
@swag_from(doc("user", "delete_account.yml"))
@jwt_required()
def delete_account():
    """
   
    """

    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)

    if not user:
        return api_error("User not found", 404)

    try:
        db.session.delete(user)
        db.session.commit()
        return api_ok(
            message="Account and all related history deleted successfully"
        )
    except Exception as e:
        db.session.rollback()
        return api_error(f"Error deleting account: {str(e)}", 500)
