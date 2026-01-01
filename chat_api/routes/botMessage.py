# bot_message.py
from datetime import datetime

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
# 🎭 Persona (System Prompt)
# ======================================================

SYSTEM_PROMPT = """
شما یک مشاور شغلی و تحلیل‌گر منابع انسانی حرفه‌ای هستید.

قوانین:
- پاسخ‌ها رسمی، دقیق و حمایتی باشند
- فقط بر اساس داده‌های ارائه‌شده پاسخ بده
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
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def detect_intent(user_text: str) -> str:
    """
    تشخیص اینکه کاربر قصد تحلیل رزومه دارد یا چت عادی
    """
    prompt = f"""
    Analyze the user input.
    If they are providing a resume/CV or asking for job recommendations based on their skills, respond with 'ANALYZE'.
    If it's a general question, greeting, or follow-up chat, respond with 'CHAT'.
    
    User Input: "{user_text}"
    Response (ONLY one word):"""
    
    response = chat_client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content.strip().upper()

def update_chat_summary(chat_id: int):
    """
    خلاصه‌سازی مکالمات برای مدیریت حافظه بلندمدت
    """
    chat = Chat.query.get(chat_id)
    # دریافت ۱۰ پیام آخر برای خلاصه‌سازی
    recent_msgs = Message.query.filter_by(chat_id=chat_id).order_by(Message.message_id.desc()).limit(10).all()
    recent_msgs.reverse()
    
    chat_history = "\n".join([f"{'User' if m.is_user else 'Bot'}: {m.content}" for m in recent_msgs])
    
    prompt = f"خلاصه کوتاه و دقیق مکالمه زیر را به فارسی بنویس تا در مراجعات بعدی استفاده شود:\n\n{chat_history}"
    
    response = chat_client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    
    chat.summary = response.choices[0].message.content.strip()
    db.session.commit()
# ======================================================
# 🧠 تحلیل رزومه و انتخاب ۳ شغل برتر
# ======================================================

def analyze_resume(user_text: str):
    conn = psycopg2.connect(DATABASE_URL)
    register_vector(conn)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT company_name, job_url, raw_text, embedding
            FROM jobs
            WHERE embedding IS NOT NULL;
        """)
        jobs = cursor.fetchall()
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S.%f")[:-4]  # صدم ثانیه
        print("START EMBED", time_str)
        if not jobs:
            yield "❌ هیچ آگهی شغلی برای مقایسه یافت نشد."
            return

        resume_embedding = get_embedding(user_text)
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S.%f")[:-4]  # صدم ثانیه
        print("END AMBED", time_str)
        scored_jobs = []

        for company, url, text, emb in jobs:
            score = cosine_similarity(resume_embedding, emb)
            scored_jobs.append({
                "company": company,
                "url": url,
                "text": text,
                "score": score
            })

        # مرتب‌سازی و انتخاب ۳ شغل برتر
        scored_jobs.sort(key=lambda x: x["score"], reverse=True)
        top_jobs = scored_jobs[:3]

        jobs_with_reviews = []

        for job in top_jobs:
            company_name = keep_only_persian(job["company"]).strip()

            cursor.execute(
                "SELECT reviews FROM public.companies WHERE name = %s;",
                (company_name,)
            )
            reviews = cursor.fetchall()

            job["reviews"] = reviews if reviews else "نظری ثبت نشده است."
            jobs_with_reviews.append(job)
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S.%f")[:-4]  # صدم ثانیه
        print("GHABL AZ SKHT GOZARESH",time_str)
        # ساخت متن گزارش
        jobs_text = ""
        for i, job in enumerate(jobs_with_reviews, start=1):
            jobs_text += f"""
==============================
🔹 شغل شماره {i}

شرکت: {job['company']}
لینک: {job['url']}
درصد تطابق: {job['score'] * 100:.1f}٪

[نظرات کاربران]
{job['reviews']}

[متن آگهی]
{job['text']}
"""

        prompt = f"""
بر اساس رزومه کاربر، ۳ موقعیت شغلی با بیشترین تطابق انتخاب شده‌اند.

{jobs_text}

گزارش حرفه‌ای شامل:
1) خلاصه هر آگهی
2) ارزیابی تطابق رزومه با هر شغل
3) تحلیل نظرات مثبت و منفی هر شرکت
4) مقایسه نهایی بین ۳ شغل
5) پیشنهاد بهترین گزینه برای اقدام به همراه دلیل
"""

        stream = chat_client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            stream=True
        )
        for event in stream:
            delta = event.choices[0].delta
            if delta and getattr(delta, "content", None):
                yield delta.content
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S.%f")[:-4]  # صدم ثانیه
        print("BAAD AZ SAKHT GOZARESH",time_str)

    finally:
        cursor.close()
        conn.close()


# ======================================================
# 🤖 تولید پاسخ بات (چت ادامه‌دار)
# ======================================================
def generate_bot_reply(chat_id: int, user_text: str):
    chat = Chat.query.get(chat_id)
    if not chat:
        yield "error", "❌ چت یافت نشد."
        return

    # ۱. تشخیص قصد کاربر (Intent Detection)
    intent = detect_intent(user_text)
    
    # ۲. ارسال سیگنال نوع پیام به لایه روت
    yield "intent", intent.lower()

    if intent == 'ANALYZE':
        # اجرای تحلیل رزومه
        for chunk in analyze_resume(user_text):
            yield "content", chunk
    else:
        # مسیر چت عادی با استفاده از حافظه
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if chat.summary:
            messages.append({"role": "system", "content": f"خلاصه مکالمات قبلی: {chat.summary}"})

        # بازیابی ۶ پیام آخر (حافظه کوتاه‌مدت)
        recent_messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.message_id.desc()).limit(6).all()
        recent_messages.reverse()

        for msg in recent_messages:
            messages.append({
                "role": "user" if msg.is_user else "assistant",
                "content": msg.content
            })

        messages.append({"role": "user", "content": user_text})

        # تولید پاسخ استریمی برای چت عادی
        stream = chat_client.chat.completions.create(
            model=GPT_MODEL,
            messages=messages,
            stream=True
        )

        for event in stream:
            delta = event.choices[0].delta
            if delta and getattr(delta, "content", None):
                yield "content", delta.content

    # ۳. عملیات پس از پاسخ (خلاصه‌سازی خودکار)
    try:
        msg_count = Message.query.filter_by(chat_id=chat_id).count()
        if msg_count > 0 and msg_count % 10 == 0:
            update_chat_summary(chat_id)
    except:
        pass # جلوگیری از قطع شدن استریم در صورت خطای دیتابیس