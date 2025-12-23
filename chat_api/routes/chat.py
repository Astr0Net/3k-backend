from flask import Blueprint, request, jsonify
from ..extensions import db
from chat_api.models.models import User, Chat, Message

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/users/<int:user_id>/chats", methods=["GET"])
def get_chats(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "user not found"}), 404

    chats = [c.to_dict() for c in user.chats]
    return jsonify({"chats": chats}), 200


@chat_bp.route("/users/<int:user_id>/chats", methods=["POST"])
def create_chat(user_id):
    """
    ساخت یک چت جدید برای کاربر.
    این روت هیچ بدنه‌ی JSON لازم ندارد و فقط یک چت با عنوان اولیه "New Chat" می‌سازد.
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "user not found"}), 404

    # نیازی به request.get_json نیست؛ تا مطمئن باشیم 400 نمی‌خوریم.
    chat = Chat(user_id=user_id, title="New Chat")
    db.session.add(chat)
    db.session.commit()

    return jsonify({"message": "chat created", "chat": chat.to_dict()}), 201

@chat_bp.route("/users/<int:user_id>/chats/<int:chat_id>", methods=["DELETE"])
def delete_chat(user_id, chat_id):
    """
    حذف یک چت متعلق به کاربر.
    """
    chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first()
    if not chat:
        return jsonify({"error": "chat not found"}), 404

    # حذف پیام‌ها (اگر مدل Message رابطه cascade ندارد)
    for msg in chat.messages:
        db.session.delete(msg)

    # حذف خود چت
    db.session.delete(chat)
    db.session.commit()

    return jsonify({"message": "chat deleted"}), 200

@chat_bp.route("/users/<int:user_id>/chats/<int:chat_id>/title", methods=["PATCH"])
def update_chat_title(user_id, chat_id):
    """
    ویرایش عنوان یک چت.
    بدنه‌ی درخواست باید شامل فیلد 'title' باشد.
    """
    chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first()
    if not chat:
        return jsonify({"error": "chat not found"}), 404

    data = request.get_json(silent=True) or {}

    new_title = data.get("title")
    if not new_title:
        return jsonify({"error": "title is required"}), 400

    chat.title = new_title
    db.session.commit()

    return jsonify({
        "message": "chat title updated",
        "chat": chat.to_dict()
    }), 200
