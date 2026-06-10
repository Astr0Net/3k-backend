from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, or_, cast
from sqlalchemy.dialects.postgresql import JSONB

from ..extensions import db
from chat_api.models import User, Job, Chat, Message
from ..utils.response_utils import api_ok, api_error
from flasgger import swag_from
from chat_api.service.docs_path import doc

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# -------------------------
# Helpers
# -------------------------

def _get_current_user():
    ident = get_jwt_identity()
    if not ident:
        return None
    try:
        user_id = int(ident)
    except (TypeError, ValueError):
        return None
    return db.session.get(User, user_id)


def _require_admin():
    user = _get_current_user()
    if not user:
        return None, api_error("invalid user", http_status=401)
    role = getattr(user, "role", None)
    if not isinstance(role, str) or role.lower() != "admin":
        return None, api_error("access denied", http_status=403)
    return user, None


# -------------------------
# Stats
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
        return api_ok(data=stats, message="admin stats retrieved", http_status=200)
    except Exception as e:
        current_app.logger.exception("Admin stats error: %s", e)
        return api_error("failed to fetch stats", http_status=500)


# -------------------------
# Users: list + search
# -------------------------

@admin_bp.route("/users", methods=["GET"])
@swag_from(doc("admin", "get_users.yml"))
@jwt_required()
def get_users():
    """
    
    """
    user, error_response = _require_admin()
    if error_response:
        return error_response

    try:
        q = request.args.get("q", "").strip()
        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(int(request.args.get("per_page", 20)), 100)

        query = db.session.query(User)

        if q:
            like = f"%{q}%"
            query = query.filter(
                or_(
                    User.username.ilike(like),
                    User.email.ilike(like),
                    User.phone_number.ilike(like),
                )
            )

        total = query.count()
        users = (
            query
            .order_by(User.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return api_ok(
            data={
                "users": [u.to_dict() for u in users],
                "total": total,
                "page": page,
                "pages": (total + per_page - 1) // per_page,
            },
            message="ok",
            http_status=200,
        )
    except Exception as e:
        current_app.logger.exception("Admin get_users error: %s", e)
        return api_error("failed to fetch users", http_status=500)


# -------------------------
# Users: delete
# -------------------------

@admin_bp.route("/users/<int:target_user_id>", methods=["DELETE"])
@swag_from(doc("admin", "delete_user.yml"))
@jwt_required()
def delete_user(target_user_id):
    """
    
    """
    admin, error_response = _require_admin()
    if error_response:
        return error_response

    if admin.user_id == target_user_id:
        return api_error("cannot delete your own account", http_status=400)

    target = db.session.get(User, target_user_id)
    if not target:
        return api_error("user not found", http_status=404)

    try:
        db.session.delete(target)
        db.session.commit()
        return api_ok(data=None, message="user deleted", http_status=200)
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Admin delete_user error: %s", e)
        return api_error("failed to delete user", http_status=500)


# -------------------------
# Jobs: list + search + filter
# -------------------------

@admin_bp.route("/jobs", methods=["GET"])
@swag_from(doc("admin", "get_jobs.yml"))
@jwt_required()
def get_jobs():
    """
    
    """
    _, error_response = _require_admin()
    if error_response:
        return error_response

    try:
        q = request.args.get("q", "").strip()
        source_site = request.args.get("source_site", "").strip()
        location = request.args.get("location", "").strip()
        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(int(request.args.get("per_page", 20)), 100)

        query = db.session.query(Job)

        if q:
            like = f"%{q}%"
            query = query.filter(
                or_(
                    Job.job_title.ilike(like),
                    Job.company_name.ilike(like),
                    Job.raw_text.ilike(like),
                )
            )

        if source_site:
            query = query.filter(Job.source_site.ilike(f"%{source_site}%"))

        if location:
            query = query.filter(Job.location.ilike(f"%{location}%"))

        total = query.count()
        jobs = (
            query
            .order_by(Job.job_id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        jobs_data = []
        for j in jobs:
            jobs_data.append({
                "job_id": j.job_id,
                "job_url": j.job_url,
                "source_site": j.source_site,
                "job_title": j.job_title,
                "company_name": j.company_name,
                "location": j.location,
                "paycheck": j.paycheck,
                "requirements": j.requirements,
                "has_embedding": j.embedding is not None,
            })

        return api_ok(
            data={
                "jobs": jobs_data,
                "total": total,
                "page": page,
                "pages": (total + per_page - 1) // per_page,
            },
            message="ok",
            http_status=200,
        )
    except Exception as e:
        current_app.logger.exception("Admin get_jobs error: %s", e)
        return api_error("failed to fetch jobs", http_status=500)


# -------------------------
# Jobs: get single
# -------------------------

@admin_bp.route("/jobs/<int:job_id>", methods=["GET"])
@swag_from(doc("admin", "get_job.yml"))
@jwt_required()
def get_job(job_id):
    """
    
    """
    _, error_response = _require_admin()
    if error_response:
        return error_response

    job = db.session.get(Job, job_id)
    if not job:
        return api_error("job not found", http_status=404)

    return api_ok(
        data={
            "job_id": job.job_id,
            "job_url": job.job_url,
            "source_site": job.source_site,
            "job_title": job.job_title,
            "company_name": job.company_name,
            "location": job.location,
            "paycheck": job.paycheck,
            "requirements": job.requirements,
            "raw_text": job.raw_text,
            "has_embedding": job.embedding is not None,
        },
        message="ok",
        http_status=200,
    )


# -------------------------
# Jobs: update
# -------------------------

@admin_bp.route("/jobs/<int:job_id>", methods=["PATCH"])
@swag_from(doc("admin", "update_job.yml"))
@jwt_required()
def update_job(job_id):
    """
    
    """
    _, error_response = _require_admin()
    if error_response:
        return error_response

    job = db.session.get(Job, job_id)
    if not job:
        return api_error("job not found", http_status=404)

    data = request.get_json(silent=True) or {}

    EDITABLE_FIELDS = ("job_title", "company_name", "location", "paycheck", "requirements", "raw_text", "source_site")
    updated = False

    for field in EDITABLE_FIELDS:
        if field in data:
            value = data[field]
            # اعتبارسنجی ساده
            if field == "requirements":
                if not isinstance(value, (list, dict, type(None))):
                    return api_error(f"requirements must be list or object", http_status=400)
            elif field != "requirements" and value is not None:
                value = str(value).strip()
                if field in ("job_title", "company_name") and not value:
                    return api_error(f"{field} cannot be empty", http_status=400)
            setattr(job, field, value)
            updated = True

    if not updated:
        return api_error("no valid fields provided", http_status=400)

    try:
        db.session.commit()
        return api_ok(
            data={
                "job_id": job.job_id,
                "job_title": job.job_title,
                "company_name": job.company_name,
                "location": job.location,
                "paycheck": job.paycheck,
                "requirements": job.requirements,
                "source_site": job.source_site,
            },
            message="job updated",
            http_status=200,
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Admin update_job error: %s", e)
        return api_error("failed to update job", http_status=500)


# -------------------------
# Jobs: delete
# -------------------------

@admin_bp.route("/jobs/<int:job_id>", methods=["DELETE"])
@swag_from(doc("admin", "delete_job.yml"))
@jwt_required()
def delete_job(job_id):
    """
    
    """
    _, error_response = _require_admin()
    if error_response:
        return error_response

    job = db.session.get(Job, job_id)
    if not job:
        return api_error("job not found", http_status=404)

    try:
        db.session.delete(job)
        db.session.commit()
        return api_ok(data=None, message="job deleted", http_status=200)
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Admin delete_job error: %s", e)
        return api_error("failed to delete job", http_status=500)