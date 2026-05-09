# chat_api/routes/landing.py
from flask import Blueprint, jsonify, current_app
from sqlalchemy import func

from ..extensions import db
from chat_api.models import User, Job, Chat, Message

from ..utils.response_utils import api_ok, api_error

landing_bp = Blueprint("landing", __name__, url_prefix="/api")


# -------------------------
# Routes
# -------------------------
@landing_bp.route("/landing", methods=["GET"])
def get_landing_data():
    """
    Get landing page data
    ---
    tags:
      - Landing
    summary: Retrieve landing page content and platform statistics
    description: Returns localized landing page content along with platform-wide statistics,
      including total users, jobs, chats, and messages.
    responses:
      200:
        description: Landing data retrieved successfully
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 200
            message:
              type: string
              example: landing data retrieved
            data:
              type: object
              properties:
                hero:
                  type: object
                problem_section:
                  type: object
                solution_section:
                  type: object
                features_section:
                  type: object
                how_it_works:
                  type: object
                stats:
                  type: object
                  properties:
                    title:
                      type: string
                    items:
                      type: array
                      items:
                        type: object
                        properties:
                          key:
                            type: string
                          label:
                            type: string
                          value:
                            type: integer
                final_cta:
                  type: object
      500:
        description: Failed to fetch landing data
    """
    try:
        stats = {
            "total_users": db.session.query(func.count(User.user_id)).scalar() or 0,
            "total_jobs": db.session.query(func.count(Job.job_id)).scalar() or 0,
            "total_chats": db.session.query(func.count(Chat.chat_id)).scalar() or 0,
            "total_messages": db.session.query(func.count(Message.message_id)).scalar() or 0,
        }

        landing_content = {
            "hero": {
                "title": "دستیار هوشمند کاریابی با هوش مصنوعی",
                "subtitle": "رزومه‌ات را تحلیل کن، آگهی‌های شغلی را امتیاز بگیر و شانس خودت را بسنج.",
                "secondary_cta": "شروع چت",
                "secondary_cta_link": "/chat",
            },
            "problem_section": {
                "title": "پیدا کردن شغل مناسب سخت‌تر از چیزی است که فکر می‌کنیم",
                "description": "در دنیای پر رقابت امروز، یافتن شغل ایده‌آل بدون ابزارهای هوشمند کار آسانی نیست.",
                "points": [
                    {
                        "title": "عدم شناخت درست از توانمندی‌ها",
                        "detail": "نمی‌دانی برای چه موقعیت‌هایی شانس بیشتری داری.",
                    },
                    {
                        "title": "آگهی‌های شغلی مبهم",
                        "detail": "توضیحات طولانی و پیچیده، تصمیم‌گیری را سخت می‌کند.",
                    },
                    {
                        "title": "عدم اطمینان از شانس موفقیت",
                        "detail": "قبل از ارسال رزومه نمی‌دانی چقدر با شغل موردنظر تطابق داری.",
                    },
                ],
            },
            "solution_section": {
                "title": "راه‌حل: یک دستیار هوشمند کنار دستت",
                "description": "این سیستم با استفاده از هوش مصنوعی، رزومه و آگهی‌های شغلی را تحلیل می‌کند و بهت می‌گوید کجا شانس بیشتری داری.",
                "steps": [
                    "رزومه‌ات را بارگذاری کن یا لینک آگهی را بده.",
                    "سیستم، مهارت‌ها و نیازمندی‌ها را تحلیل می‌کند.",
                    "امتیاز تطابق، گپ مهارتی و پیشنهادهای بهبود را دریافت کن.",
                ],
            },
            "features_section": {
                "title": "قابلیت‌های اصلی",
                "features": [
                    {
                        "key": "resume_analysis",
                        "title": "تحلیل رزومه با AI",
                        "description": "شناسایی مهارت‌ها، نقاط قوت و ضعف رزومه و پیشنهاد بهبود.",
                    },
                    {
                        "key": "job_scoring",
                        "title": "امتیازدهی به آگهی شغلی",
                        "description": "محاسبه درصد تطابق رزومه با هر آگهی شغلی و نمایش مهارت‌های هم‌پوشان و گپ‌ها.",
                    },
                    {
                        "key": "ai_chat",
                        "title": "چت هوشمند کاریابی",
                        "description": "پرسش‌وپاسخ درباره مسیر شغلی، مهارت‌های لازم و آمادگی برای مصاحبه.",
                    },
                    {
                        "key": "requirement_analysis",
                        "title": "تحلیل نیازمندی‌های شغل",
                        "description": "استخراج مهارت‌های ضروری و ترجیحی از متن آگهی شغلی.",
                    },
                    {
                        "key": "company_reviews",
                        "title": "بررسی شرکت‌ها",
                        "description": "نمای کلی از تجربه دیگران و فضای کاری شرکت‌ها.",
                    },
                ],
            },
            "how_it_works": {
                "title": "چطور کار می‌کند؟",
                "steps": [
                    {
                        "step": 1,
                        "title": "ورود اطلاعات",
                        "description": "رزومه را تایپ کن.",
                    },
                    {
                        "step": 2,
                        "title": "تحلیل با هوش مصنوعی",
                        "description": "سیستم، داده‌ها را پردازش و مزایا را تحلیل می‌کند.",
                    },
                    {
                        "step": 3,
                        "title": "دریافت نتایج",
                        "description": "امتیاز تطابق، راهکارهای بهبود و پیشنهادهای شغلی را ببین.",
                    },
                ],
            },
            "stats": {
                "title": "چقدر تا الان استفاده شده؟",
                "items": [
                    {
                        "key": "total_users",
                        "label": "تعداد کاربران ثبت‌شده",
                        "value": stats["total_users"],
                    },
                    {
                        "key": "total_jobs",
                        "label": "تعداد آگهی‌های پردازش‌شده",
                        "value": stats["total_jobs"],
                    },
                    {
                        "key": "total_chats",
                        "label": "تعداد چت‌های انجام‌شده",
                        "value": stats["total_chats"],
                    },
                    {
                        "key": "total_messages",
                        "label": "تعداد پیام‌های پردازش‌شده",
                        "value": stats["total_messages"],
                    },
                ],
            },
            "final_cta": {
                "title": "شغل بعدی‌ات را هوشمندانه انتخاب کن",
                "secondary_cta": "شروع چت",
                "secondary_cta_link": "/chat",
            },
        }

        return api_ok(
            data=landing_content,
            message="landing data retrieved",
            http_status=200,
        )

    except Exception as e:
        current_app.logger.exception("Landing data error: %s", e)
        return api_error("failed to fetch landing data", http_status=500)
