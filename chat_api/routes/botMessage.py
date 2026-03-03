from chat_api.models import Chat, Message
from ..extensions import db

from .qom_llm import qom_chat, chunk_text
from .intent_classifier import detect_intent
from .resume_report import analyze_resume_stream
from .memory_summary import maybe_update_chat_summary


SYSTEM_PROMPT = """
شما یک مشاور شغلی و تحلیل‌گر منابع انسانی حرفه‌ای هستید.

قوانین:
- پاسخ‌ها رسمی، دقیق و حمایتی باشند
- فقط بر اساس داده‌های ارائه‌شده پاسخ بده
- از حدس، اغراق و اطلاعات ساختگی خودداری کن
- زبان پاسخ‌ها فارسی باشد
- از ساخت جدول برای مقایسه خودداری کن فقط متن بنویس
""".strip()


def generate_bot_reply(chat_id: int, user_text: str, user_id: int | None = None):
    q = Chat.query.filter_by(chat_id=chat_id)
    if user_id is not None:
        q = q.filter_by(user_id=user_id)

    chat = q.first()
    if not chat:
        yield "intent", "error"
        yield "content", "❌ چت یافت نشد یا دسترسی ندارید."
        return

    intent = detect_intent(user_text)
    yield "intent", "analyze" if intent == "ANALYZE" else "chat"

    if intent == "ANALYZE":
        for item in analyze_resume_stream(user_text):
            if isinstance(item, tuple) and len(item) == 2:
                yield item[0], item[1]
            else:
                yield "content", item
        return

    # ---- CHAT MODE ----
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # حافظه بلندمدت
    if chat.summary:
        messages.append({"role": "system", "content": f"خلاصه مکالمات قبلی: {chat.summary}"})

    # حافظه کوتاه‌مدت: ۶ پیام آخر
    recent_messages = (
        Message.query
        .filter_by(chat_id=chat_id)
        .order_by(Message.message_id.desc())
        .limit(6)
        .all()
    )
    recent_messages.reverse()

    for msg in recent_messages:
        messages.append({
            "role": "user" if msg.is_user else "assistant",
            "content": msg.content
        })

    messages.append({"role": "user", "content": user_text})

    reply = qom_chat(messages)

    for part in chunk_text(reply, chunk_size=220):
        yield "content", part

    # اختیاری: هر ۱۰ پیام خلاصه را آپدیت کن
    try:
        maybe_update_chat_summary(chat_id, user_id=user_id, every_n_messages=10)
    except Exception:
        pass