from flask_jwt_extended import get_jwt_identity
from chat_api.models.chat import Chat

def current_user_id() -> int:
    return int(get_jwt_identity())

def chat_brief(chat: Chat) -> dict:
    return {
        "chat_id": chat.chat_id,
        "title": chat.title,
        "created_at": chat.created_at.isoformat() if chat.created_at else None,
        "updated_at": chat.updated_at.isoformat() if getattr(chat, "updated_at", None) else None,
    }

def get_chat_if_owner(chat_id: int, user_id: int):
    return Chat.query.filter_by(chat_id=chat_id, user_id=user_id).first()
