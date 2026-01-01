from flask import Blueprint, request, jsonify, Response, stream_with_context
from ..extensions import db
from chat_api.models.models import Chat, Message
from .botMessage import generate_bot_reply, chat_client, GPT_MODEL
import re
from datetime import datetime

message_bp = Blueprint("message", __name__)

def generate_ai_title(content: str) -> str:
    """
    تولید یک عنوان کوتاه و مرتبط با استفاده از هوش مصنوعی
    """
    try:
        # استفاده از مدل برای جنریت تایتل بر اساس اولین پیام
        prompt = f"بر اساس پیام زیر، یک عنوان بسیار کوتاه (حداکثر ۳ کلمه) برای این گفتگو بساز. فقط خود عنوان را برگردان:\n\n{content}"
        response = chat_client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
            temperature=0.7
        )
        return response.choices[0].message.content.strip().replace('"', '')
    except Exception:
        return "چت جدید"

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

    # ۱) ذخیره پیام کاربر
    user_msg = Message(
        chat_id=chat_id,
        content=content,
        time=Message.now_as_string(),
        is_user=True
    )
    db.session.add(user_msg)

    # به‌روزرسانی عنوان با هوش مصنوعی (فقط اگر عنوان پیش‌فرض باشد)
    if not chat.title or chat.title == "New Chat":
        chat.title = generate_ai_title(content)

    # کامیت کردن برای دریافت ID پیام کاربر و ثبت تایتل قبل از شروع استریم
    db.session.commit()

    def event_stream():
        full_text = ""
        try:
            # دریافت ژنراتور پاسخ بات
            reply_gen = generate_bot_reply(chat_id, content)
            
            # دریافت اولین خروجی (Intent Tag)
            # خروجی اول به صورت ("intent", "analyze" یا "chat") است
            tag, intent_type = next(reply_gen)
            
            # ارسال رویداد meta شامل نوع پاسخ برای تفکیک در فرانت‌اِند
            yield f"event: meta\ndata: {{\"chat_id\": {chat_id}, \"user_message_id\": {user_msg.message_id}, \"type\": \"{intent_type}\"}}\n\n"

            # ۲) استریم محتوا (Content Chunks)
            for tag, chunk in reply_gen:
                if tag == "content" and chunk:
                    full_text += chunk
                    yield f"data: {chunk}\n\n"

            # ۳) ذخیره پیام بات بعد از اتمام کامل استریم
            bot_msg = Message(
                chat_id=chat_id,
                content=full_text,
                time=Message.now_as_string(),
                is_user=False
            )
            db.session.add(bot_msg)
            db.session.commit()

            yield f"event: done\ndata: {{\"bot_message_id\": {bot_msg.message_id}}}\n\n"

        except Exception as e:
            db.session.rollback()
            yield f"event: error\ndata: {{\"message\": \"{str(e)}\"}}\n\n"

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )