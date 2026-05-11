from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..extensions import db
from chat_api.models import Chat

from ..utils.response_utils import api_ok, api_error
from ..utils.chat_utils import chat_brief, current_user_id, get_chat_if_owner
from flasgger import swag_from
from chat_api.docs_path import doc
chat_bp = Blueprint("chat", __name__)




@chat_bp.route("/chats", methods=["GET"])
@swag_from(doc("chat", "get_chats.yml"))
@jwt_required()
def get_chats():
    """
    
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
@swag_from(doc("chat", "create_chats.yml"))
@jwt_required()
def create_chat():
    """
    
    """
    user_id = current_user_id()

    chat = Chat(user_id=user_id, title="New Chat")
    db.session.add(chat)
    db.session.commit()

    data = {"chat": chat_brief(chat)}
    return api_ok(data=data, message="chat created", http_status=201)


@chat_bp.route("/chats/<int:chat_id>", methods=["DELETE"])
@swag_from(doc("chat", "delete_chats.yml"))
@jwt_required()
def delete_chat(chat_id):
    """
    
    """
    user_id = current_user_id()

    chat = get_chat_if_owner(chat_id, user_id)

    if not chat:
        return api_error("chat not found", 404)

    db.session.delete(chat)
    db.session.commit()

    return api_ok(data=None, message="chat deleted", http_status=200)


@chat_bp.route("/chats/<int:chat_id>/title", methods=["PATCH"])
@swag_from(doc("chat", "update_chat_title.yml"))
@jwt_required()
def update_chat_title(chat_id):
    """
    
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
