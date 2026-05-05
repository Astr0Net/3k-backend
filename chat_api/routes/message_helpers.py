import json
from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from chat_api.models import Chat, Message


def api_ok(data=None, message="ok", http_status=200):
    payload = {"status": http_status, "message": message, "data": data}
    return jsonify(payload), http_status


def api_error(message="error", http_status=400, data=None):
    payload = {"status": http_status, "error": message, "data": data}
    return jsonify(payload), http_status


def current_user_id() -> int:
    return int(get_jwt_identity())


def chat_brief(chat: Chat) -> dict:
    return {
        "chat_id": chat.chat_id,
        "title": chat.title,
        "created_at": chat.created_at.isoformat() if chat.created_at else None,
        "updated_at": chat.updated_at.isoformat() if getattr(chat, "updated_at", None) else None,
    }


def message_dto(m: Message) -> dict:
    return {
        "message_id": m.message_id,
        "content": m.content,
        "created_at": m.created_at.isoformat() if m.created_at else None,
        "role": m.role,
    }


def get_chat_if_owner(chat_id: int, user_id: int):
    return Chat.query.filter_by(chat_id=chat_id, user_id=user_id).first()


def sse(event: str, payload: dict):
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
