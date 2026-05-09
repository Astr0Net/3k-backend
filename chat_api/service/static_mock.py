import json
from chat_api.models import Message
from ..extensions import db
from ..utils.message_utils import sse, chat_brief

STATIC_BOT_TEXT = (
    "گزارش تست سامانه پیشنهاد شغل\n"
    "---------------------------------\n"
    "این پاسخ در حالت تست استاتیک تولید شده است. در این حالت هیچ مدل هوش مصنوعی "
    "یا سرویس خارجی فراخوانی نمی‌شود و هدف آن صرفاً بررسی عملکرد کامل سیستم است.\n\n"
    "در این تست موارد زیر بررسی می‌شوند:\n"
    "1. ذخیره شدن پیام کاربر در دیتابیس\n"
    "2. ارسال صحیح رویدادهای SSE از سمت سرور\n"
    "3. دریافت و رندر پیام بات در رابط کاربری\n"
    "4. نمایش کارت‌های شغلی با ساختار واقعی API\n"
    "5. تست تعاملات UI مانند کلیک روی لینک شغل یا مشاهده جزئیات\n\n"
    "کارت‌های شغلی نمایش داده شده در ادامه داده‌های نمونه هستند که برای تست "
    "فرانت‌اند و جریان کامل سیستم تولید شده‌اند.\n"
)

STATIC_JOBS = [
    {
        "title": "Python Backend Developer",
        "company_name": "Demo Company",
        "location": "Remote",
        "paycheck": "Negotiable",
        "requirements": [
            "Python",
            "Flask",
            "REST API Development",
            "SQL / PostgreSQL",
            "Docker",
            "Git"
        ],
        "match_percent": 96,
        "job_url": "https://example.com/jobs/python-backend",
        "source_site": "LinkedIn",
        "company_reviews": {
            "rating": 4.2,
            "reviews_count": 120,
            "summary": "محیط کاری مناسب برای توسعه‌دهندگان بک‌اند با تیم فنی فعال."
        }
    },
    {
        "title": "Backend Engineer (APIs)",
        "company_name": "Test Startup",
        "location": "Tehran",
        "paycheck": "40M - 60M Toman",
        "requirements": [
            "Python",
            "FastAPI",
            "Microservices",
            "PostgreSQL",
            "Redis",
            "CI/CD"
        ],
        "match_percent": 91,
        "job_url": "https://example.com/jobs/backend-engineer",
        "source_site": "Jobinja",
        "company_reviews": {
            "rating": 3.9,
            "reviews_count": 54,
            "summary": "استارتاپ در حال رشد با تمرکز بر توسعه سرویس‌های مقیاس‌پذیر."
        }
    },
    {
        "title": "Junior Data Engineer",
        "company_name": "Sample Tech",
        "location": "Hybrid",
        "paycheck": "30M - 45M Toman",
        "requirements": [
            "Python",
            "ETL Pipelines",
            "Airflow",
            "SQL",
            "Data Warehousing",
            "Linux"
        ],
        "match_percent": 87,
        "job_url": "https://example.com/jobs/data-engineer",
        "source_site": "Indeed",
        "company_reviews": {
            "rating": 4.0,
            "reviews_count": 78,
            "summary": "شرکت داده‌محور با تمرکز بر تحلیل و پردازش داده‌های بزرگ."
        }
    }
]


def stream_static_reply(chat, user_msg, user_text: str, user_id: int, title_changed: bool):
    """
    Static SSE stream without any LLM usage.
    Keeps the same event order expected by the frontend:
    intent -> meta -> jobs -> content -> done
    """
    try:
        # 1) intent
        intent_type = "CHAT"
        yield sse("intent", {"type": intent_type})

        # 2) meta
        yield sse(
            "meta",
            {
                "chat": chat_brief(chat),
                "user_message_id": user_msg.message_id,
                "type": intent_type,
                "title_changed": title_changed,
            },
        )

        # 3) jobs (optional but kept for UI compatibility)
        yield sse("jobs", {"items": STATIC_JOBS})

        # 4) content
        yield sse("content", {"delta": STATIC_BOT_TEXT})

        # 5) save assistant message
        bot_msg = Message(
            chat_id=chat.chat_id,
            content=STATIC_BOT_TEXT,
            time=Message.now_as_string(),
            is_user=False,
        )
        db.session.add(bot_msg)
        db.session.commit()

        # 6) done
        yield sse("done", {"bot_message_id": bot_msg.message_id})

    except Exception as e:
        db.session.rollback()
        yield sse("error", {"message": str(e)})
