from chat_api.models import Chat, Message
from ..extensions import db
from .qom_llm import qom_chat

SUMMARY_SYSTEM = """
You are a memory manager for a job-search assistant chatbot.
Your only job is to create and update a concise conversation summary in Persian.
Output ONLY the summary text. No explanation. No preamble.
""".strip()

SUMMARY_PROMPT_TEMPLATE = """
وظیفه: خلاصه حافظه مکالمه را به‌روز کن.

## خلاصه فعلی:
{previous_summary}

## پیام‌های جدید:
{new_block}

## قوانین خلاصه‌سازی:
- حداکثر ۱۵۰ کلمه
- فقط اطلاعات مهم را نگه دار: هدف کاربر، مهارت‌های ذکرشده، سوالات کلیدی، تصمیم‌ها
- اطلاعات تکراری یا بی‌ربط را حذف کن
- اگر خلاصه قبلی وجود دارد، آن را با اطلاعات جدید ادغام کن — همه چیز را از نو ننویس
- زبان: فارسی
- فرمت: چند جمله پیوسته، بدون bullet point
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
        [f"{m.role}: {(m.content or '').strip()[:300]}" for m in new_msgs]
    )
    previous_summary = (chat.summary or "ندارد").strip()

    prompt = SUMMARY_PROMPT_TEMPLATE.format(
        previous_summary=previous_summary,
        new_block=new_block,
    )

    try:
        summary = qom_chat(
            [
                {"role": "system", "content": SUMMARY_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=280,
        )
    except Exception:
        return

    summary = (summary or "").strip()
    if not summary:
        return

    chat.summary = summary
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