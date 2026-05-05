from flask import Blueprint, request, Response, stream_with_context
from flask_jwt_extended import jwt_required

from ..extensions import db
from chat_api.models import Message

from .title_gen import generate_chat_title
from .message_helpers import (
    api_ok, api_error,
    current_user_id, get_chat_if_owner,
    chat_brief, message_dto,
)
from .message_stream import stream_bot_reply
from .static_mock import stream_static_reply #test


message_bp = Blueprint("message", __name__)


@message_bp.route("/chats/<int:chat_id>/messages", methods=["GET"])
@jwt_required()
def get_messages(chat_id):
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

    data = {"chat": chat_brief(chat), "messages": [message_dto(m) for m in messages]}
    return api_ok(data=data, message="ok", http_status=200)


@message_bp.route("/chats/<int:chat_id>/messages", methods=["POST"])
@jwt_required()
def create_message(chat_id):
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

    return Response(
        stream_with_context(stream_static_reply(chat, user_msg, content, user_id, title_changed)),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

    return Response(
        stream_with_context(stream_bot_reply(chat, user_msg, content, user_id, title_changed)),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
