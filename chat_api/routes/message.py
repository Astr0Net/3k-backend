from flask import Blueprint, request, Response, stream_with_context
from flask_jwt_extended import jwt_required

from ..extensions import db
from chat_api.models import Message
from chat_api.models.job_card import JobCard
from chat_api.service.static_mock import STATIC_JOB_ITEMS

from ..service.title_gen import generate_chat_title
from ..service.message_stream import stream_bot_reply
from ..service.static_mock import stream_static_reply

from ..utils.chat_utils import chat_brief, current_user_id, get_chat_if_owner
from ..utils.response_utils import api_ok, api_error
from ..utils.message_utils import message_dto

from flasgger import swag_from
from chat_api.service.docs_path import doc

message_bp = Blueprint("message", __name__)

# True = static/offline mode | False = live LLM mode
STATIC_MODE = True


@message_bp.route("/chats/<int:chat_id>/messages", methods=["GET"])
@swag_from(doc("message", "get_messages.yml"))
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

    messages_data = []
    for m in message_dto_list(messages, static_mode=STATIC_MODE):
        messages_data.append(m)

    data = {
        "chat": chat_brief(chat),
        "messages": messages_data,
    }
    return api_ok(data=data, message="ok", http_status=200)


def message_dto_list(messages: list, static_mode: bool) -> list:
    result = []
    for m in messages:
        dto = message_dto(m)

        if m.role == "assistant":
            if static_mode:
                # حالت استاتیک: همیشه همان کارت‌های ثابت
                dto["job_cards"] = STATIC_JOB_ITEMS
            else:
                # حالت live: از DB بخوان
                card_row = JobCard.query.filter_by(message_id=m.message_id).first()
                dto["job_cards"] = card_row.cards_json if card_row else None

        result.append(dto)
    return result


@message_bp.route("/chats/<int:chat_id>/messages", methods=["POST"])
@swag_from(doc("message", "create_message.yml"))
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

    stream_fn = stream_static_reply if STATIC_MODE else stream_bot_reply

    return Response(
        stream_with_context(
            stream_fn(chat, user_msg, content, user_id, title_changed)
        ),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )