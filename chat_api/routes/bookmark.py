from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from chat_api.extensions import db
from chat_api.models.bookmark import Bookmark
from chat_api.utils.response_utils import api_ok, api_error
from flasgger import swag_from
from chat_api.service.docs_path import doc

bookmark_bp = Blueprint("bookmark", __name__)


# -------------------------
# Toggle bookmark (add / remove)
# -------------------------
@bookmark_bp.route("/bookmarks/toggle", methods=["POST"])
@swag_from(doc("bookmark", "toggle_bookmark.yml"))
@jwt_required()
def toggle_bookmark():
    """
    اگر بوک‌مارک وجود داشت حذف می‌کند؛ اگر نداشت اضافه می‌کند.
    """
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    job_url = (data.get("job_url") or "").strip()
    if not job_url:
        return api_error("job_url is required", 400)

    existing = Bookmark.query.filter_by(user_id=user_id, job_url=job_url).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        return api_ok(
            data={"bookmarked": False, "job_url": job_url},
            message="bookmark removed",
            http_status=200,
        )

    bookmark = Bookmark(
        user_id=user_id,
        job_url=job_url,
        job_title=(data.get("job_title") or "").strip() or None,
        company_name=(data.get("company_name") or "").strip() or None,
        location=(data.get("location") or "").strip() or None,
        paycheck=(data.get("paycheck") or "").strip() or None,
        source_site=(data.get("source_site") or "").strip() or None,
        match_percent=data.get("match_percent"),
        requirements=data.get("requirements"),
        company_reviews=data.get("company_reviews"),
    )

    db.session.add(bookmark)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return api_error("already bookmarked", 409)

    return api_ok(
        data={"bookmarked": True, "id": bookmark.id, "job_url": job_url},
        message="bookmark added",
        http_status=201,
    )


# -------------------------
# List bookmarks
# -------------------------
@bookmark_bp.route("/bookmarks", methods=["GET"])
@swag_from(doc("bookmark", "list_bookmarks.yml"))
@jwt_required()
def list_bookmarks():
    """
    لیست تمام بوک‌مارک‌های کاربر، مرتب‌شده از جدیدترین.
    """
    user_id = int(get_jwt_identity())

    bookmarks = (
        Bookmark.query
        .filter_by(user_id=user_id)
        .order_by(Bookmark.created_at.desc())
        .all()
    )

    return api_ok(
        data={"bookmarks": [b.to_dict() for b in bookmarks]},
        message="ok",
        http_status=200,
    )


# -------------------------
# Delete bookmark by id
# -------------------------
@bookmark_bp.route("/bookmarks/<int:bookmark_id>", methods=["DELETE"])
@swag_from(doc("bookmark", "delete_bookmark.yml"))
@jwt_required()
def delete_bookmark(bookmark_id):
    """
    حذف بوک‌مارک با id.
    """
    user_id = int(get_jwt_identity())

    bookmark = Bookmark.query.filter_by(id=bookmark_id, user_id=user_id).first()
    if not bookmark:
        return api_error("bookmark not found", 404)

    db.session.delete(bookmark)
    db.session.commit()

    return api_ok(data=None, message="bookmark deleted", http_status=200)


# -------------------------
# Check if a job_url is bookmarked
# -------------------------
@bookmark_bp.route("/bookmarks/check", methods=["GET"])
@swag_from(doc("bookmark", "check_bookmark.yml"))
@jwt_required()
def check_bookmark():
    """
    بررسی می‌کند آیا یک job_url بوک‌مارک شده یا نه.
    """
    user_id = int(get_jwt_identity())
    job_url = (request.args.get("job_url") or "").strip()

    if not job_url:
        return api_error("job_url query param is required", 400)

    bookmark = Bookmark.query.filter_by(user_id=user_id, job_url=job_url).first()

    return api_ok(
        data={
            "bookmarked": bookmark is not None,
            "id": bookmark.id if bookmark else None,
            "job_url": job_url,
        },
        message="ok",
        http_status=200,
    )