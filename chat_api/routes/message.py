from flask import Blueprint, request, jsonify
from ..extensions import db
from chat_api.models.models import Chat, Message
from .botMessage import generate_bot_reply
import re

message_bp = Blueprint("message", __name__)

STOP_WORDS = {
    "من", "میخوام", "می‌خوام", "میخواهم", "لطفا", "سلام",
    "یه", "یک", "در", "با", "برای", "از", "که", "و", "یا"
}

def generate_title_from_content(content: str, max_len: int = 40) -> str:
    if not content:
        return "New Chat"

    text = content.strip()
    text = re.sub(r"\s+", " ", text)

    text = re.split(r"[.!؟\n]", text)[0]

    text = re.sub(r"[^\u0600-\u06FF0-9\s]", "", text)

    words = text.split()

    while words and words[0] in STOP_WORDS:
        words.pop(0)

    if not words:
        return "New Chat"

    title = " ".join(words)

    if len(title) > max_len:
        title = title[:max_len].rstrip() + "…"

    return title



@message_bp.route("/chats/<int:chat_id>/messages", methods=["GET"])
def get_messages(chat_id):
    chat = Chat.query.get(chat_id)
    if not chat:
        return jsonify({"error": "chat not found"}), 404

    return jsonify({
        "chat": chat.to_dict(),
        "messages": [m.to_dict() for m in chat.messages]
    }), 200


@message_bp.route("/chats/<int:chat_id>/messages", methods=["POST"])
def create_message(chat_id):
    chat = Chat.query.get(chat_id)
    if not chat:
        return jsonify({"error": "chat not found"}), 404

    data = request.get_json(silent=True) or {}
    content = data.get("content")

    if not content:
        return jsonify({"error": "content is required"}), 400

    # =========================
    # پیام کاربر
    # =========================
    user_msg = Message(
        chat_id=chat_id,
        content=content,
        time=Message.now_as_string(),
        is_user=True
    )
    db.session.add(user_msg)

    # اگر چت تازه است، عنوان بساز
    if not chat.title or chat.title == "New Chat":
        chat.title = generate_title_from_content(content)

    # 🔴 مهم: قبل از پاسخ بات، پیام کاربر ثبت شود
    db.session.flush()

    # =========================
    # پاسخ بات (با حافظه)
    # =========================
    bot_reply_text = generate_bot_reply(chat_id, content)

    bot_msg = Message(
        chat_id=chat_id,
        content=bot_reply_text,
        time=Message.now_as_string(),
        is_user=False
    )
    db.session.add(bot_msg)

    db.session.commit()

    return jsonify({
        "user_message": user_msg.to_dict(),
        "bot_reply": bot_msg.to_dict()
    }), 201
