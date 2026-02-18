import json
from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from chat_api.models.models import Chat, Message
from .botMessage import generate_bot_reply, chat_client, GPT_MODEL

message_bp = Blueprint("message", __name__)


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
    return int(get_jwt_identity())


def _chat_brief(chat: Chat) -> dict:
    return {
        "chat_id": chat.chat_id,
        "title": chat.title,
    }


def _message_dto(m: Message) -> dict:
    return {
        "message_id": m.message_id,
        "content": m.content,
        "time": m.time,
        "role": "user" if m.is_user else "assistant",
    }


def generate_ai_title(content: str) -> str:
    try:
        prompt = (
            "بر اساس پیام زیر، یک عنوان بسیار کوتاه (حداکثر ۳ کلمه) برای این گفتگو بساز. "
            "فقط خود عنوان را برگردان:\n\n"
            f"{content}"
        )
        response = chat_client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
            temperature=0.7
        )
        return (response.choices[0].message.content or "").strip().replace('"', '') or "چت جدید"
    except Exception:
        return "چت جدید"


def _get_chat_if_owner(chat_id: int, user_id: int):
    # این روش هم امن‌تره، هم اطلاعات اضافه لو نمی‌ده
    return Chat.query.filter_by(chat_id=chat_id, user_id=user_id).first()


# -------------------------
# Routes
# -------------------------
@message_bp.route("/chats/<int:chat_id>/messages", methods=["GET"])
@jwt_required()
def get_messages(chat_id):
    user_id = _current_user_id()
    chat = _get_chat_if_owner(chat_id, user_id)
    if not chat:
        return api_error("chat not found", 404)

    messages = (
        Message.query
        .filter_by(chat_id=chat_id)
        .order_by(Message.message_id.asc())
        .all()
    )

    # فقط چیزهای لازم
    data = {
        "chat": _chat_brief(chat),
        "messages": [_message_dto(m) for m in messages],
    }
    return api_ok(data=data, message="ok", http_status=200)


@message_bp.route("/chats/<int:chat_id>/messages", methods=["POST"])
@jwt_required()
def create_message(chat_id):
    user_id = _current_user_id()
    chat = _get_chat_if_owner(chat_id, user_id)
    if not chat:
        return api_error("chat not found", 404)

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return api_error("content is required", 400)

    user_msg = Message(
        chat_id=chat_id,
        content=content,
        time=Message.now_as_string(),
        is_user=True
    )
    db.session.add(user_msg)

    # عنوان فقط وقتی لازم است ساخته شود
    title_changed = False
    if not chat.title or chat.title == "New Chat":
        new_title = generate_ai_title(content)
        if new_title and new_title != chat.title:
            chat.title = new_title
            title_changed = True

    db.session.commit()

    def sse(event: str, payload: dict):
        # payload همیشه JSON باشد تا فرانت یکدست parse کند
        return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

    def event_stream():
        full_text = ""
        try:
            # ✅ enforce مالکیت در botMessage هم
            reply_gen = generate_bot_reply(chat_id, content, user_id=user_id)

            # اولین yield باید intent باشد
            tag, intent_type = next(reply_gen)

            yield sse("meta", {
                "chat": _chat_brief(chat),
                "user_message_id": user_msg.message_id,
                "type": intent_type,          # chat | analyze | error
                "title_changed": title_changed
            })

            # stream chunks
            for tag, chunk in reply_gen:
                if tag == "content" and chunk:
                    full_text += chunk
                    yield sse("delta", {"text": chunk})

            bot_msg = Message(
                chat_id=chat_id,
                content=full_text,
                time=Message.now_as_string(),
                is_user=False
            )
            db.session.add(bot_msg)
            db.session.commit()

            yield sse("done", {"bot_message_id": bot_msg.message_id})

        except Exception as e:
            db.session.rollback()
            # خطا هم JSON استاندارد داخل SSE
            yield sse("error", {"message": str(e)})

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )
