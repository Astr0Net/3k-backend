from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from ..extensions import db
from chat_api.models import User, Job, Chat, Message

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# -------------------------
# Response helpers (Standard API Contract)
# -------------------------
def api_ok(data=None, message="ok", http_status=200):
    payload = {
        "status": http_status,
        "message": message,
        "data": data,
    }
    return jsonify(payload), http_status


def api_error(message="error", http_status=400, data=None):
    payload = {
        "status": http_status,
        "error": message,
        "data": data,
    }
    return jsonify(payload), http_status


# -------------------------
# Helpers
# -------------------------
def _current_user_id() -> int:
    ident = get_jwt_identity()
    if ident is None:
        raise ValueError("missing jwt identity")
    return int(ident)


def _is_admin() -> bool:
    """
    بررسی نقش ادمین
    اولویت: user.role == "admin"
    fallback: username == "admin"
    """
    user_id = _current_user_id()
    user = db.session.get(User, user_id)
    if not user:
        return False

    role = getattr(user, "role", None)
    if isinstance(role, str) and role.lower() == "admin":
        return True

    return getattr(user, "username", None) == "admin"


# -------------------------
# Routes
# -------------------------
@admin_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_dashboard_stats():
    """
    Get admin dashboard statistics
    ---
    tags:
      - Admin
    summary: Get overall platform statistics (admin only)
    description: >
      Returns high-level statistics about the platform, including
      total users, jobs, chats, and messages.
      This endpoint is restricted to admin users and requires a valid JWT token.
    security:
      - BearerAuth: []
    responses:
      200:
        description: Admin statistics retrieved successfully
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 200
            message:
              type: string
              example: "admin stats retrieved"
            data:
              type: object
              properties:
                total_users:
                  type: integer
                  example: 42
                total_jobs:
                  type: integer
                  example: 15
                total_chats:
                  type: integer
                  example: 120
                total_messages:
                  type: integer
                  example: 845
      401:
        description: Missing or invalid JWT token
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 401
            error:
              type: string
              example: "missing token: Authorization header is expected"
            data:
              type: object
              nullable: true
      403:
        description: Access denied (user is not admin)
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 403
            error:
              type: string
              example: "access denied"
            data:
              type: object
              nullable: true
      500:
        description: Internal server error while fetching stats
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 500
            error:
              type: string
              example: "failed to fetch stats"
            data:
              type: object
              nullable: true
    """
    if not _is_admin():
        return api_error("access denied", http_status=403)

    try:
        stats = {
            "total_users": db.session.query(func.count(User.user_id)).scalar() or 0,
            "total_jobs": db.session.query(func.count(Job.job_id)).scalar() or 0,
            "total_chats": db.session.query(func.count(Chat.chat_id)).scalar() or 0,
            "total_messages": db.session.query(func.count(Message.message_id)).scalar() or 0,
        }
        return api_ok(data=stats, message="admin stats retrieved", http_status=200)

    except Exception as e:
        current_app.logger.exception("Admin stats error: %s", e)
        return api_error("failed to fetch stats", http_status=500)
