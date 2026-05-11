from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from chat_api.extensions import db
from chat_api.models.resume import Resume
from flasgger import swag_from
from chat_api.docs_path import doc
resume_bp = Blueprint("resume", __name__, url_prefix="/resumes")


# -------------------------
# create resume
# -------------------------
@resume_bp.route("/", methods=["POST"])
@swag_from(doc("resume", "create_resume.yml"))
@jwt_required()
def create_resume():
    """
    
    """
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()

    if not title:
        return jsonify({"error": "title is required"}), 400

    if not content:
        return jsonify({"error": "content is required"}), 400

    resume = Resume(user_id=user_id, title=title, content=content)

    db.session.add(resume)
    db.session.commit()

    return jsonify({
        "message": "resume created successfully",
        "data": {
            "id": resume.id,
            "title": resume.title,
            "content": resume.content,
            "created_at": resume.created_at.isoformat(),
            "updated_at": resume.updated_at.isoformat()
        }
    }), 201


# -------------------------
# list resumes
# -------------------------
@resume_bp.route("/", methods=["GET"])
@swag_from(doc("resume", "list_resumes.yml"))
@jwt_required()
def list_resumes():
    """
   
    """
    user_id = get_jwt_identity()

    resumes = (
        Resume.query
        .filter_by(user_id=user_id)
        .order_by(Resume.updated_at.desc())
        .all()
    )

    return jsonify({
        "data": [
            {
                "id": resume.id,
                "title": resume.title,
                "created_at": resume.created_at.isoformat(),
                "updated_at": resume.updated_at.isoformat()
            }
            for resume in resumes
        ]
    }), 200


# -------------------------
# get single resume
# -------------------------
@resume_bp.route("/<int:resume_id>", methods=["GET"])
@swag_from(doc("resume", "get_resume.yml"))
@jwt_required()
def get_resume(resume_id):
    """
    
    """
    user_id = get_jwt_identity()

    resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()

    if not resume:
        return jsonify({"error": "resume not found"}), 404

    return jsonify({
        "data": {
            "id": resume.id,
            "title": resume.title,
            "content": resume.content,
            "created_at": resume.created_at.isoformat(),
            "updated_at": resume.updated_at.isoformat()
        }
    }), 200


# -------------------------
# update resume
# -------------------------
@resume_bp.route("/<int:resume_id>", methods=["PUT", "PATCH"])
@swag_from(doc("resume", "update_resume.yml"))
@jwt_required()
def update_resume(resume_id):
    """
    
    """
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()

    if not resume:
        return jsonify({"error": "resume not found"}), 404

    if "title" in data:
        title = (data.get("title") or "").strip()
        if not title:
            return jsonify({"error": "title cannot be empty"}), 400
        resume.title = title

    if "content" in data:
        content = (data.get("content") or "").strip()
        if not content:
            return jsonify({"error": "content cannot be empty"}), 400
        resume.content = content

    db.session.commit()

    return jsonify({
        "message": "resume updated successfully",
        "data": {
            "id": resume.id,
            "title": resume.title,
            "content": resume.content,
            "created_at": resume.created_at.isoformat(),
            "updated_at": resume.updated_at.isoformat()
        }
    }), 200


# -------------------------
# delete resume
# -------------------------
@resume_bp.route("/<int:resume_id>", methods=["DELETE"])
@swag_from(doc("resume", "delete_resume.yml"))
@jwt_required()
def delete_resume(resume_id):
    """
   
    """
    user_id = get_jwt_identity()

    resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()

    if not resume:
        return jsonify({"error": "resume not found"}), 404

    db.session.delete(resume)
    db.session.commit()

    return jsonify({"message": "resume deleted successfully"}), 200


# -------------------------
# import resume content
# -------------------------
@resume_bp.route("/<int:resume_id>/import", methods=["GET"])
@swag_from(doc("resume", "import_resume_content.yml"))
@jwt_required()
def import_resume_content(resume_id):
    """
    
    """
    user_id = get_jwt_identity()

    resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()

    if not resume:
        return jsonify({"error": "resume not found"}), 404

    return jsonify({"data": {"content": resume.content}}), 200
