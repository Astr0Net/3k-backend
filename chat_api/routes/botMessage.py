# bot_message.py

import re
import psycopg2
import numpy as np
from openai import OpenAI
from pgvector.psycopg2 import register_vector

from config import Config
from chat_api.models.models import Chat, Message
from ..extensions import db


# ======================================================
# تنظیمات کلاینت‌ها
# ======================================================

DATABASE_URL = Config.SQLALCHEMY_DATABASE_URI

embedding_client = OpenAI(
    base_url=Config.LIARA_EMBEDDING_BASE_URL,
    api_key=Config.LIARA_EMBEDDING_API_KEY
)

chat_client = OpenAI(
    base_url=Config.LIARA_CHAT_BASE_URL,
    api_key=Config.LIARA_CHAT_API_KEY
)

EMBEDDING_MODEL = Config.EMBEDDING_MODEL
GPT_MODEL = Config.GPT_MODEL


# ======================================================
# 🎭 نقش (Persona) – فقط یک بار
# ======================================================

SYSTEM_PROMPT = """
شما یک مشاور شغلی و تحلیل‌گر منابع انسانی حرفه‌ای هستید.

قوانین:
- پاسخ‌ها رسمی، دقیق و حمایتی باشند
- فقط بر اساس اطلاعات مکالمه و داده‌های ارائه‌شده پاسخ بده
- از حدس، اغراق و اطلاعات ساختگی خودداری کن
- زبان پاسخ‌ها فارسی باشد
"""


# ======================================================
# توابع کمکی
# ======================================================

def keep_only_persian(text: str) -> str:
    return re.sub(r"[^\u0600-\u06FF\u200c\s]", "", text or "")


def get_embedding(text: str):
    resp = embedding_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
        encoding_format="float"
    )
    return resp.data[0].embedding


def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


# ======================================================
# 🧠 تحلیل رزومه و پیدا کردن بهترین شغل
# ======================================================

def analyze_resume(user_text: str) -> str:
    conn = psycopg2.connect(DATABASE_URL)
    register_vector(conn)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, company_name, job_url, raw_text, embedding
            FROM jobs
            WHERE embedding IS NOT NULL;
        """)
        jobs = cursor.fetchall()
        if not jobs:
            return "❌ هیچ آگهی شغلی برای مقایسه یافت نشد."

        resume_embedding = get_embedding(user_text)

        best_job = None
        best_score = -1

        for job_id, company, url, text, emb in jobs:
            score = cosine_similarity(resume_embedding, emb)
            if score > best_score:
                best_score = score
                best_job = {
                    "company": company,
                    "url": url,
                    "text": text,
                    "score": score
                }

        company_name = keep_only_persian(best_job["company"]).strip()

        cursor.execute(
            "SELECT reviews FROM public.companies WHERE name = %s;",
            (company_name,)
        )
        reviews = cursor.fetchall()

        prompt = f"""
[آگهی شغلی]
شرکت: {best_job['company']}
لینک: {best_job['url']}

[نظرات کاربران]
{reviews if reviews else "نظری ثبت نشده است."}

[متن آگهی]
{best_job['text']}

[درصد تطابق]
{best_job['score'] * 100:.1f}٪

گزارش حرفه‌ای شامل:
1) خلاصه آگهی
2) ارزیابی تطابق رزومه
3) جمع‌بندی نظرات مثبت و منفی
4) توصیه نهایی
"""

        response = chat_client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content

    finally:
        cursor.close()
        conn.close()


# ======================================================
# 🤖 تولید پاسخ بات (چت ادامه‌دار)
# ======================================================

def generate_bot_reply(chat_id: int, user_text: str) -> str:
    chat = Chat.query.get(chat_id)
    if not chat:
        return "❌ چت یافت نشد."

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # حافظه بلندمدت
    if chat.summary:
        messages.append({
            "role": "system",
            "content": f"خلاصه مکالمه تا اینجا:\n{chat.summary}"
        })

    # حافظه کوتاه‌مدت
    recent = (
        Message.query
        .filter_by(chat_id=chat_id)
        .order_by(Message.message_id.desc())
        .limit(6)
        .all()
    )
    recent.reverse()

    for msg in recent:
        messages.append({
            "role": "user" if msg.is_user else "assistant",
            "content": msg.content
        })

    # تشخیص درخواست تحلیل رزومه
    if "رزومه" in user_text and "تحلیل" in user_text:
        analysis = analyze_resume(user_text)
        return analysis

    # پیام جدید
    messages.append({"role": "user", "content": user_text})

    response = chat_client.chat.completions.create(
        model=GPT_MODEL,
        messages=messages
    )

    return response.choices[0].message.content
