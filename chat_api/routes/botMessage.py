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
""".strip()


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


def cosine_similarity(a, b) -> float:
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def detect_intent(user_text: str) -> str:
    """
    تشخیص اینکه کاربر قصد تحلیل رزومه دارد یا چت عادی
    خروجی فقط: ANALYZE یا CHAT
    """
    prompt = f"""
Analyze the user input.
If they are providing a resume/CV or asking for job recommendations based on their skills, respond with ANALYZE.
If it's a general question, greeting, or follow-up chat, respond with CHAT.

User Input: "{user_text}"

Response (ONLY one word):"""

    response = chat_client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    raw = (response.choices[0].message.content or "").strip().upper()

    if "ANALYZE" in raw:
        return "ANALYZE"
    return "CHAT"


def update_chat_summary(chat_id: int, user_id: int | None = None):
    """
    خلاصه‌سازی مکالمات برای مدیریت حافظه بلندمدت

    نکته امنیتی:
    اگر user_id داده شود، خلاصه فقط برای چتی آپدیت می‌شود که متعلق به همان user باشد.
    """
    q = Chat.query.filter_by(chat_id=chat_id)
    if user_id is not None:
        q = q.filter_by(user_id=user_id)

    chat = q.first()
    if not chat:
        return

    recent_msgs = (
        Message.query
        .filter_by(chat_id=chat_id)
        .order_by(Message.message_id.desc())
        .limit(10)
        .all()
    )
    recent_msgs.reverse()

    chat_history = "\n".join(
        [f"{'User' if m.is_user else 'Bot'}: {m.content}" for m in recent_msgs]
    )

    prompt = (
        "خلاصه کوتاه و دقیق مکالمه زیر را به فارسی بنویس "
        "تا در مراجعات بعدی استفاده شود:\n\n"
        f"{chat_history}"
    )

    response = chat_client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    chat.summary = (response.choices[0].message.content or "").strip()
    db.session.commit()


# ======================================================
# 🧠 تحلیل رزومه و انتخاب ۳ شغل برتر
# ======================================================

def analyze_resume(user_text: str):
    """
    خروجی: chunkهای متنی (string) برای استریم
    """
    conn = None
    cursor = None

    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=8)
        register_vector(conn)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT company_name, job_url, raw_text, embedding
            FROM jobs
            WHERE embedding IS NOT NULL;
        """)
        jobs = cursor.fetchall()

        if not jobs:
            yield "❌ هیچ آگهی شغلی برای مقایسه یافت نشد."
            return

        resume_embedding = get_embedding(user_text)

        scored_jobs = []
        for company, url, text, emb in jobs:
            try:
                score = cosine_similarity(resume_embedding, emb)
            except Exception:
                score = 0.0

            scored_jobs.append({
                "company": company,
                "url": url,
                "text": text,
                "score": score
            })

        scored_jobs.sort(key=lambda x: x["score"], reverse=True)
        top_jobs = scored_jobs[:3]

        jobs_with_reviews = []
        for job in top_jobs:
            raw_company = (job.get("company") or "").strip()
            company_name = keep_only_persian(raw_company).strip()
            query_name = company_name if company_name else raw_company

            cursor.execute(
                "SELECT reviews FROM public.companies WHERE name = %s;",
                (query_name,)
            )
            rows = cursor.fetchall()

            if rows:
                reviews_text = "\n".join([r[0] for r in rows if r and r[0]])
                job["reviews"] = reviews_text.strip() if reviews_text.strip() else "نظری ثبت نشده است."
            else:
                job["reviews"] = "نظری ثبت نشده است."

            jobs_with_reviews.append(job)

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
""".strip()

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

    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass


# ======================================================
# 🤖 تولید پاسخ بات (چت ادامه‌دار)
# ======================================================

def generate_bot_reply(chat_id: int, user_text: str, user_id: int | None = None):
    """
    قرارداد خروجی برای message.py:
      - اولین yield حتماً: ("intent", "chat|analyze|error")
      - بعدش: ("content", "<chunk>")...

    نکته امنیتی:
      - اگر user_id داده شود، چت فقط در صورت مالکیت همان user قابل دسترسی است.
    """
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
        for chunk in analyze_resume(user_text):
            yield "content", chunk
        return

    # مسیر چت عادی با حافظه
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if chat.summary:
        messages.append({"role": "system", "content": f"خلاصه مکالمات قبلی: {chat.summary}"})

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

    stream = chat_client.chat.completions.create(
        model=GPT_MODEL,
        messages=messages,
        stream=True
    )

    for event in stream:
        delta = event.choices[0].delta
        if delta and getattr(delta, "content", None):
            yield "content", delta.content
