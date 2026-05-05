from chat_api.models import Chat, Message

from .qom_llm import qom_chat, chunk_text
from .intent_classifier import detect_intent
from .resume_report import analyze_resume_stream


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

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if chat.summary:
        messages.append({
            "role": "system",
            "content": f"خلاصه مکالمات قبلی: {chat.summary}"
        })

    recent_messages = (
        Message.query
        .filter_by(chat_id=chat_id)
        .order_by(Message.created_at.desc())
        .limit(6)
        .all()
    )
    recent_messages.reverse()

    for msg in recent_messages:
        role = msg.role if msg.role in {"user", "assistant", "system"} else ("user" if getattr(msg, "is_user", False) else "assistant")
        content = (msg.content or "").strip()

        if not content:
            continue

        messages.append({
            "role": role,
            "content": content
        })

    cleaned_user_text = (user_text or "").strip()
    if not cleaned_user_text:
        yield "content", "❌ پیام کاربر خالی است."
        return

    messages.append({"role": "user", "content": cleaned_user_text})

    reply = qom_chat(messages)

    if not reply or not str(reply).strip():
        yield "content", "❌ پاسخی از مدل دریافت نشد."
        return

    for part in chunk_text(str(reply).strip(), chunk_size=220):
        if part:
            yield "content", part
