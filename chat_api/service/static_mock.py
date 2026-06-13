import time
from datetime import datetime, timezone

from chat_api.models import Message
from ..extensions import db
from ..utils.message_utils import sse
from ..utils.chat_utils import chat_brief


STATIC_REPORT_INTRO = "✅ ۳ آگهی پیشنهادی از دیتابیس پیدا شد. در حال آماده‌سازی گزارش..."
STATIC_REPORT_BODY = (
    "۱) خلاصه آگهی‌ها:\n"
    "- Backend Developer: تمرکز روی توسعه API و بهینه‌سازی سرویس‌ها\n"
    "- Data Engineer: تمرکز روی ساخت پایپلاین داده و ETL\n"
    "- ML Engineer: تمرکز روی پیاده‌سازی مدل‌ها و سرویس‌دهی آنها\n\n"
    "۲) ارزیابی تطبیق:\n"
    "با توجه به مهارت‌های قابل برداشت از متن کاربر، بیشترین تطبیق با نقش Backend است؛ "
    "نقش Data Engineer در صورت داشتن تجربه پایپلاین/ETL توصیه می‌شود؛ "
    "نقش ML Engineer مناسب‌تر است اگر تجربه NLP/LLM و استقرار مدل دارید.\n\n"
    "۳) پیشنهاد نهایی:\n"
    "اگر هدف ورود سریع‌تر به بازار و استفاده از مهارت‌های فعلی است، Backend انتخاب اول است."
)

STATIC_JOB_ITEMS = [
    {
        "title": "Python Backend Developer",
        "company_name": "Acme Co",
        "location": "Tehran",
        "paycheck": "Negotiable",
        "requirements": [
            "Python",
            "Flask",
            "SQLAlchemy",
            "REST API",
            "PostgreSQL",
            "Docker",
        ],
        "match_percent": 86,
        "job_url": "https://example.com/jobs/1",
        "source_site": "mock",
        "company_reviews": {
            "summary": "محیط حرفه‌ای با فرصت رشد",
            "rating": 4.2,
            "pros": ["تیم خوب", "فرصت رشد"],
            "cons": ["فشار کاری مقطعی"],
        },
    },
    {
        "title": "Data Engineer",
        "company_name": "Example Ltd",
        "location": "Remote",
        "paycheck": "120M - 160M",
        "requirements": ["Python", "SQL", "ETL", "Airflow", "Data Modeling"],
        "match_percent": 74,
        "job_url": "https://example.com/jobs/2",
        "source_site": "mock",
        "company_reviews": None,
    },
    {
        "title": "ML Engineer",
        "company_name": "QomAI",
        "location": "Qom",
        "paycheck": "-",
        "requirements": ["Python", "NLP", "LLM APIs", "Vector Search", "MLOps basics"],
        "match_percent": 69,
        "job_url": "https://example.com/jobs/3",
        "source_site": "mock",
        "company_reviews": {
            "summary": "محصول جذاب، نیاز به خودمدیریتی",
            "rating": 4.0,
        },
    },
]


def _chunk_text(text: str, chunk_size: int = 220):
    text = text or ""
    for i in range(0, len(text), chunk_size):
        part = text[i:i + chunk_size]
        if part:
            yield part


def get_static_cards_for_message(message_id: int) -> list:
    """
    در حالت static، همیشه همان STATIC_JOB_ITEMS برمی‌گردد.
    message_id فقط برای یکپارچگی امضا است.
    """
    return STATIC_JOB_ITEMS


def stream_static_reply(chat, user_msg, user_text: str, user_id: int, title_changed: bool):
    """
    SSE stream - static/offline mode.
    کارت‌ها در DB ذخیره نمی‌شوند؛ همیشه از STATIC_JOB_ITEMS سرو می‌شوند.
    """
    full_text = ""

    try:
        intent_type = "analyze"

        yield sse("meta", {
            "chat": chat_brief(chat),
            "user_message_id": user_msg.message_id,
            "type": intent_type,
            "title_changed": title_changed,
        })

        full_text += STATIC_REPORT_INTRO
        yield sse("content", {"delta": STATIC_REPORT_INTRO})
        time.sleep(0.03)

        yield sse("jobs", {"items": STATIC_JOB_ITEMS})

        report_body = "\n\n" + STATIC_REPORT_BODY
        for part in _chunk_text(report_body, chunk_size=220):
            full_text += part
            yield sse("content", {"delta": part})
            time.sleep(0.03)

        if not full_text.strip():
            yield sse("error", {"message": "empty bot content"})
            return

        bot_msg = Message(
            chat_id=chat.chat_id,
            content=full_text.strip(),
            role="assistant",
        )
        db.session.add(bot_msg)

        if hasattr(chat, "updated_at"):
            chat.updated_at = datetime.now(timezone.utc)

        db.session.commit()

        yield sse("done", {"bot_message_id": bot_msg.message_id})

    except Exception as e:
        db.session.rollback()
        yield sse("error", {"message": str(e)})