from flask import Blueprint, request, Response, stream_with_context
from flask_jwt_extended import jwt_required

from ..extensions import db
from chat_api.models import Message

from ..service.title_gen import generate_chat_title
from ..service.message_stream import stream_bot_reply
from ..service.static_mock import stream_static_reply  # test

from ..utils.chat_utils import chat_brief, current_user_id, get_chat_if_owner
from ..utils.response_utils import api_ok, api_error
from ..utils.message_utils import message_dto


message_bp = Blueprint("message", __name__)


@message_bp.route("/chats/<int:chat_id>/messages", methods=["GET"])
@jwt_required()
def get_messages(chat_id):
    """
    Get all messages of a chat
    ---
    tags:
      - Message
    summary: Get all messages of a chat
    description: Returns all messages for a chat that belongs to the authenticated user, ordered by creation time ascending.
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: chat_id
        type: integer
        required: true
        description: ID of the chat
    responses:
      200:
        description: Messages retrieved successfully
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
                chat:
                  type: object
                  properties:
                    chat_id:
                      type: integer
                      example: 1
                    title:
                      type: string
                      example: Job Search Chat
                    created_at:
                      type: string
                      format: date-time
                    updated_at:
                      type: string
                      format: date-time
                messages:
                  type: array
                  items:
                    type: object
                    properties:
                      message_id:
                        type: integer
                        example: 10
                      chat_id:
                        type: integer
                        example: 1
                      role:
                        type: string
                        example: user
                      content:
                        type: string
                        example: "سلام، برای این موقعیت شغلی چقدر مناسبم؟"
                      created_at:
                        type: string
                        format: date-time
      401:
        description: Missing or invalid JWT token
      404:
        description: Chat not found
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 404
            error:
              type: string
              example: chat not found
            data:
              type: string
              nullable: true
      500:
        description: Internal server error
    """
    user_id = current_user_id()
    chat = get_chat_if_owner(chat_id, user_id)
    if not chat:
        return api_error("chat not found", 404)

    messages = (
        Message.query
        .filter_by(chat_id=chat_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    data = {
        "chat": chat_brief(chat),
        "messages": [message_dto(m) for m in messages],
    }
    return api_ok(data=data, message="ok", http_status=200)


@message_bp.route("/chats/<int:chat_id>/messages", methods=["POST"])
@jwt_required()
def create_message(chat_id):
    """
    Create a user message and receive streamed assistant response
    ---
    tags:
      - Message
    summary: Create a user message and receive streamed assistant response
    description: >
      Creates a new user message in the specified chat, optionally updates the chat
      title if it is still the default title, and returns a streamed Server-Sent
      Events (SSE) response containing the assistant reply.
    security:
      - BearerAuth: []
    consumes:
      - application/json
    produces:
      - text/event-stream
    parameters:
      - in: path
        name: chat_id
        type: integer
        required: true
        description: ID of the chat
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - content
          properties:
            content:
              type: string
              example: "برای این آگهی شغلی چه مهارت‌هایی لازم دارم؟"
    responses:
      200:
        description: Stream started successfully and assistant response is returned as SSE
        schema:
          type: string
          example: |
            event: message
            data: {"chunk":"سلام"}

            event: message
            data: {"chunk":"، حتما"}

            event: done
            data: {"message":"completed"}
      400:
        description: Content is required
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 400
            error:
              type: string
              example: content is required
            data:
              type: string
              nullable: true
      401:
        description: Missing or invalid JWT token
      404:
        description: Chat not found
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 404
            error:
              type: string
              example: chat not found
            data:
              type: string
              nullable: true
      500:
        description: Internal server error during streaming
    """
    user_id = current_user_id()
    chat = get_chat_if_owner(chat_id, user_id)
    if not chat:
        return api_error("chat not found", 404)

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return api_error("content is required", 400)

    user_msg = Message(
        chat_id=chat_id,
        content=content,
        role="user",
    )
    db.session.add(user_msg)

    title_changed = False
    if not chat.title or chat.title in ("New Chat", "چت جدید"):
        new_title = generate_chat_title(content)
        if new_title and new_title != chat.title:
            chat.title = new_title
            title_changed = True

    db.session.commit()

    # برای تست از stream_static_reply استفاده شده؛ اگر خواستی ریل‌تایم باشه،
    # فقط stream_static_reply رو با stream_bot_reply عوض کن.
    return Response(
        stream_with_context(
            # stream_static_reply(chat, user_msg, content, user_id, title_changed)
            # در صورت نیاز:
            stream_bot_reply(chat, user_msg, content, user_id, title_changed)
        ),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
