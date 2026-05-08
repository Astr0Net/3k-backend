from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from chat_api.extensions import db
from chat_api.models.resume import Resume

resume_bp = Blueprint("resume", __name__, url_prefix="/resumes")


# -------------------------
# create resume
# -------------------------
@resume_bp.route("/", methods=["POST"])
@jwt_required()
def create_resume():
    """
    Create resume
    ---
    tags:
      - Resume
    summary: Create a new resume for the authenticated user
    description: Creates a new resume with a title and content for the authenticated user.
    security:
      - BearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - title
            - content
          properties:
            title:
              type: string
              example: "رزومه برنامه نویس بک اند"
            content:
              type: string
              example: "تجربه 3 سال برنامه نویسی پایتون و Flask"
    responses:
      201:
        description: Resume created successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "resume created successfully"
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                title:
                  type: string
                  example: "رزومه برنامه نویس بک اند"
                content:
                  type: string
                  example: "تجربه 3 سال برنامه نویسی پایتون و Flask"
                created_at:
                  type: string
                  example: "2026-05-08T15:00:00"
                updated_at:
                  type: string
                  example: "2026-05-08T15:00:00"
      400:
        description: Validation error
        schema:
          type: object
          properties:
            error:
              type: string
              example: "title is required"
      401:
        description: Missing or invalid JWT token
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
@jwt_required()
def list_resumes():
    """
    List resumes
    ---
    tags:
      - Resume
    summary: List all resumes of the authenticated user
    description: Returns all resumes owned by the authenticated user ordered by updated time descending.
    security:
      - BearerAuth: []
    responses:
      200:
        description: List of resumes
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  title:
                    type: string
                    example: "رزومه برنامه نویس بک اند"
                  created_at:
                    type: string
                    example: "2026-05-08T15:00:00"
                  updated_at:
                    type: string
                    example: "2026-05-08T15:00:00"
      401:
        description: Missing or invalid JWT token
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
@jwt_required()
def get_resume(resume_id):
    """
    Get single resume
    ---
    tags:
      - Resume
    summary: Get a specific resume by ID
    description: Returns a single resume owned by the authenticated user.
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: resume_id
        type: integer
        required: true
        description: Resume ID
    responses:
      200:
        description: Resume retrieved successfully
        schema:
          type: object
          properties:
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                title:
                  type: string
                  example: "رزومه برنامه نویس بک اند"
                content:
                  type: string
                  example: "محتوای رزومه"
                created_at:
                  type: string
                  example: "2026-05-08T15:00:00"
                updated_at:
                  type: string
                  example: "2026-05-08T15:00:00"
      404:
        description: Resume not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: "resume not found"
      401:
        description: Missing or invalid JWT token
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
@jwt_required()
def update_resume(resume_id):
    """
    Update resume
    ---
    tags:
      - Resume
    summary: Update an existing resume
    description: Updates the title or content of a resume owned by the authenticated user.
    security:
      - BearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: path
        name: resume_id
        type: integer
        required: true
        description: Resume ID
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
              example: "رزومه به روز شده"
            content:
              type: string
              example: "محتوای جدید رزومه"
    responses:
      200:
        description: Resume updated successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "resume updated successfully"
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                title:
                  type: string
                  example: "رزومه به روز شده"
                content:
                  type: string
                  example: "محتوای جدید رزومه"
                created_at:
                  type: string
                  example: "2026-05-08T15:00:00"
                updated_at:
                  type: string
                  example: "2026-05-08T15:00:00"
      400:
        description: Validation error
        schema:
          type: object
          properties:
            error:
              type: string
              example: "title cannot be empty"
      404:
        description: Resume not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: "resume not found"
      401:
        description: Missing or invalid JWT token
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
@jwt_required()
def delete_resume(resume_id):
    """
    Delete resume
    ---
    tags:
      - Resume
    summary: Delete a resume
    description: Deletes a resume owned by the authenticated user.
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: resume_id
        type: integer
        required: true
        description: Resume ID
    responses:
      200:
        description: Resume deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "resume deleted successfully"
      404:
        description: Resume not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: "resume not found"
      401:
        description: Missing or invalid JWT token
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
@jwt_required()
def import_resume_content(resume_id):
    """
    Import resume content
    ---
    tags:
      - Resume
    summary: Get resume content for import
    description: Returns only the content of a resume owned by the authenticated user.
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: resume_id
        type: integer
        required: true
        description: Resume ID
    responses:
      200:
        description: Resume content retrieved successfully
        schema:
          type: object
          properties:
            data:
              type: object
              properties:
                content:
                  type: string
                  example: "متن کامل رزومه"
      404:
        description: Resume not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: "resume not found"
      401:
        description: Missing or invalid JWT token
    """
    user_id = get_jwt_identity()

    resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()

    if not resume:
        return jsonify({"error": "resume not found"}), 404

    return jsonify({"data": {"content": resume.content}}), 200
