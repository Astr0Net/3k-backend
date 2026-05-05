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
