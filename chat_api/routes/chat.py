from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..extensions import db
from chat_api.models import Chat

from ..utils.response_utils import api_ok, api_error
from ..utils.chat_utils import chat_brief, current_user_id, get_chat_if_owner

chat_bp = Blueprint("chat", __name__)




@chat_bp.route("/chats", methods=["GET"])
@jwt_required()
def get_chats():
    """
    Get user chats
    ---
    tags:
      - Chat
    summary: Get all chats for the authenticated user
    security:
      - BearerAuth: []
    responses:
      200:
        description: List of user chats
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 200
            message:
              type: string
              example: ok
            data:
              type: object
              properties:
                chats:
                  type: array
                  items:
                    type: object
                    properties:
                      chat_id:
                        type: integer
                        example: 1
                      title:
                        type: string
                        example: New Chat
                      created_at:
                        type: string
                        format: date-time
                      updated_at:
                        type: string
                        format: date-time
      401:
        description: Missing or invalid JWT token
    """
    user_id = current_user_id()

    chats = (
        db.session.query(Chat)
        .filter(Chat.user_id == user_id)
        .order_by(Chat.updated_at.desc(), Chat.chat_id.desc())
        .all()
    )

    data = {"chats": [chat_brief(c) for c in chats]}
    return api_ok(data=data, message="ok", http_status=200)


@chat_bp.route("/chats", methods=["POST"])
@jwt_required()
def create_chat():
    """
    Create chat
    ---
    tags:
      - Chat
    summary: Create a new chat for the authenticated user
    security:
      - BearerAuth: []
    responses:
      201:
        description: Chat created successfully
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 201
            message:
              type: string
              example: chat created
            data:
              type: object
              properties:
                chat:
                  type: object
                  properties:
                    chat_id:
                      type: integer
                    title:
                      type: string
                    created_at:
                      type: string
                      format: date-time
                    updated_at:
                      type: string
                      format: date-time
      401:
        description: Missing or invalid JWT token
    """
    user_id = current_user_id()

    chat = Chat(user_id=user_id, title="New Chat")
    db.session.add(chat)
    db.session.commit()

    data = {"chat": chat_brief(chat)}
    return api_ok(data=data, message="chat created", http_status=201)


@chat_bp.route("/chats/<int:chat_id>", methods=["DELETE"])
@jwt_required()
def delete_chat(chat_id):
    """
    Delete chat
    ---
    tags:
      - Chat
    summary: Delete a chat owned by the authenticated user
    security:
      - BearerAuth: []
    parameters:
      - name: chat_id
        in: path
        required: true
        type: integer
        description: ID of the chat to delete
    responses:
      200:
        description: Chat deleted successfully
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 200
            message:
              type: string
              example: chat deleted
            data:
              type: object
              nullable: true
      404:
        description: Chat not found
      401:
        description: Missing or invalid JWT token
    """
    user_id = current_user_id()

    chat = get_chat_if_owner(chat_id, user_id)

    if not chat:
        return api_error("chat not found", 404)

    db.session.delete(chat)
    db.session.commit()

    return api_ok(data=None, message="chat deleted", http_status=200)


@chat_bp.route("/chats/<int:chat_id>/title", methods=["PATCH"])
@jwt_required()
def update_chat_title(chat_id):
    """
    Update chat title
    ---
    tags:
      - Chat
    summary: Update the title of a chat
    security:
      - BearerAuth: []
    consumes:
      - application/json
    parameters:
      - name: chat_id
        in: path
        required: true
        type: integer
        description: ID of the chat
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - title
          properties:
            title:
              type: string
              example: Job Search Discussion
    responses:
      200:
        description: Chat title updated
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 200
            message:
              type: string
              example: chat title updated
            data:
              type: object
              properties:
                chat:
                  type: object
                  properties:
                    chat_id:
                      type: integer
                    title:
                      type: string
                    created_at:
                      type: string
                      format: date-time
                    updated_at:
                      type: string
                      format: date-time
      400:
        description: Invalid title
      404:
        description: Chat not found
      401:
        description: Missing or invalid JWT token
    """
    user_id = current_user_id()

    chat = get_chat_if_owner(chat_id, user_id)

    if not chat:
        return api_error("chat not found", 404)

    data = request.get_json(silent=True) or {}
    new_title = (data.get("title") or "").strip()

    if not new_title:
        return api_error("title is required", 400)
    if len(new_title) > 60:
        return api_error("title is too long (max 60 chars)", 400)

    chat.title = new_title
    db.session.commit()

    data = {"chat": chat_brief(chat)}
    return api_ok(data=data, message="chat title updated", http_status=200)
