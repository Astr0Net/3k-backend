from flask import Blueprint, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from ..extensions import db
from chat_api.models import User, Job, Chat, Message
from ..utils.response_utils import api_ok, api_error
from flasgger import swag_from
from chat_api.docs_path import doc
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# -------------------------
# Helpers
# -------------------------

def _get_current_user():
    """
    Safely fetch current user from JWT identity.
    """
    ident = get_jwt_identity()
    if not ident:
        return None

    try:
        user_id = int(ident)
    except (TypeError, ValueError):
        return None

    return db.session.get(User, user_id)


def _require_admin():
    """
    Ensure current user has admin role.
    """
    user = _get_current_user()
    if not user:
        return None, api_error("invalid user", http_status=401)

    role = getattr(user, "role", None)
    if not isinstance(role, str) or role.lower() != "admin":
        return None, api_error("access denied", http_status=403)

    return user, None


# -------------------------
# Routes
# -------------------------

@admin_bp.route("/stats", methods=["GET"])
@swag_from(doc("admin", "get_dashboard_stats.yml"))
@jwt_required()
def get_dashboard_stats():
    """
    
    """
    user, error_response = _require_admin()
    if error_response:
        return error_response

    try:
        stats = {
            "total_users": db.session.query(func.count(User.user_id)).scalar() or 0,
            "total_jobs": db.session.query(func.count(Job.job_id)).scalar() or 0,
            "total_chats": db.session.query(func.count(Chat.chat_id)).scalar() or 0,
            "total_messages": db.session.query(func.count(Message.message_id)).scalar() or 0,
        }

        return api_ok(
            data=stats,
            message="admin stats retrieved",
            http_status=200,
        )

    except Exception as e:
        current_app.logger.exception("Admin stats error: %s", e)
        return api_error("failed to fetch stats", http_status=500)
