from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..extensions import db
from chat_api.models import Chat


chat_bp = Blueprint("chat", __name__)


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


def _current_user_id() -> int:
    return int(get_jwt_identity())


def _chat_brief(chat: Chat) -> dict:
    return {
        "chat_id": chat.chat_id,
        "title": chat.title,
        "created_at": chat.created_at.isoformat() if chat.created_at else None,
        "updated_at": chat.updated_at.isoformat() if getattr(chat, "updated_at", None) else None,
    }


@chat_bp.route("/chats", methods=["GET"])
@jwt_required()
def get_chats():
    user_id = _current_user_id()

    chats = (
        db.session.query(Chat)
        .filter(Chat.user_id == user_id)
        .order_by(Chat.updated_at.desc(), Chat.chat_id.desc())
        .all()
    )

    data = {"chats": [_chat_brief(c) for c in chats]}
    return api_ok(data=data, message="ok", http_status=200)


@chat_bp.route("/chats", methods=["POST"])
@jwt_required()
def create_chat():
    user_id = _current_user_id()

    chat = Chat(user_id=user_id, title="New Chat")
    db.session.add(chat)
    db.session.commit()

    data = {"chat": _chat_brief(chat)}
    return api_ok(data=data, message="chat created", http_status=201)


@chat_bp.route("/chats/<int:chat_id>", methods=["DELETE"])
@jwt_required()
def delete_chat(chat_id):
    user_id = _current_user_id()

    chat = (
        db.session.query(Chat)
        .filter(Chat.chat_id == chat_id, Chat.user_id == user_id)
        .first()
    )
    if not chat:
        return api_error("chat not found", 404)

    db.session.delete(chat)
    db.session.commit()

    return api_ok(data=None, message="chat deleted", http_status=200)


@chat_bp.route("/chats/<int:chat_id>/title", methods=["PATCH"])
@jwt_required()
def update_chat_title(chat_id):
    user_id = _current_user_id()

    chat = (
        db.session.query(Chat)
        .filter(Chat.chat_id == chat_id, Chat.user_id == user_id)
        .first()
    )
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

    data = {"chat": _chat_brief(chat)}
    return api_ok(data=data, message="chat title updated", http_status=200)
