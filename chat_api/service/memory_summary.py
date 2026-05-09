from chat_api.models import Chat, Message
from ..extensions import db
from .qom_llm import qom_chat

SYSTEM_PROMPT = """
شما یک مشاور شغلی و تحلیل‌گر منابع انسانی حرفه‌ای هستید.
پاسخ‌ها فارسی، دقیق، بدون حدس و ساختگی.
""".strip()


def update_chat_summary(chat_id: int, user_id: int | None = None, chunk_limit: int = 18):
    q = Chat.query.filter_by(chat_id=chat_id)
    if user_id is not None:
        q = q.filter_by(user_id=user_id)

    chat = q.first()
    if not chat:
        return

    last_id = chat.last_summarized_message_id or 0

    new_msgs = (
        Message.query
        .filter(Message.chat_id == chat_id, Message.message_id > last_id)
        .order_by(Message.created_at.asc())
        .limit(chunk_limit)
        .all()
    )
    if not new_msgs:
        return

    new_block = "\n".join(
        [f"{m.role}: {m.content}" for m in new_msgs]
    )
    previous_summary = (chat.summary or "").strip()

    prompt = f"""
تو باید یک خلاصه‌ی حافظه‌ای کوتاه و دقیق از مکالمه بسازی و همیشه به‌روز نگهش داری.

خلاصه قبلی:
\"\"\"{previous_summary}\"\"\"

پیام‌های جدید:
\"\"\"{new_block}\"\"\"

قواعد:
- خروجی فقط خودِ خلاصه باشد
- فارسی، کوتاه، شامل نکات مهم/هدف/تصمیم‌ها
""".strip()

    try:
        summary = qom_chat(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=260
        )
    except Exception:
        return

    chat.summary = (summary or "").strip()
    chat.last_summarized_message_id = new_msgs[-1].message_id
    db.session.commit()


def maybe_update_chat_summary(chat_id: int, user_id: int | None = None, every_n_messages: int = 10):
    q = Chat.query.filter_by(chat_id=chat_id)
    if user_id is not None:
        q = q.filter_by(user_id=user_id)

    chat = q.first()
    if not chat:
        return

    total = Message.query.filter_by(chat_id=chat_id).count()
    if total % every_n_messages != 0:
        return

    update_chat_summary(chat_id, user_id=user_id)
