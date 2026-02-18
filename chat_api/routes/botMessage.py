import re
import psycopg2
import numpy as np
from google import genai
from google.genai import types
from pgvector.psycopg2 import register_vector

from config import Config
from chat_api.models.models import Chat, Message
from ..extensions import db


# ======================================================
# تنظیمات
# ======================================================

DATABASE_URL = Config.SQLALCHEMY_DATABASE_URI

if not Config.GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set")

client = genai.Client(api_key=Config.GEMINI_API_KEY)

CHAT_MODEL = Config.GEMINI_CHAT_MODEL
EMBEDDING_MODEL = Config.GEMINI_EMBEDDING_MODEL


# ======================================================
# 🎭 Persona
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
# Helpers
# ======================================================

def keep_only_persian(text: str) -> str:
    return re.sub(r"[^\u0600-\u06FF\u200c\s]", "", text or "")


def get_embedding(text: str, task_type: str):
    resp = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(task_type=task_type),
    )
    return np.array(resp.embeddings[0].values, dtype=float)


def cosine_similarity(a, b) -> float:
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def clamp_percent(score: float) -> int:
    try:
        p = int(round(float(score) * 100))
    except Exception:
        p = 0
    return max(0, min(100, p))


def detect_intent(user_text: str) -> str:
    prompt = f"""
ورودی کاربر را تحلیل کن.
اگر کاربر رزومه/CV داده یا درخواست معرفی شغل بر اساس مهارت‌ها و رزومه دارد: ANALYZE
اگر گفتگو عمومی/سلام/سوال عمومی/پیگیری گفتگو است: CHAT

متن کاربر:
\"\"\"{user_text}\"\"\"

فقط یکی از این دو کلمه را برگردان:
ANALYZE
CHAT
""".strip()

    resp = client.models.generate_content(
        model=CHAT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0,
            max_output_tokens=10,
            system_instruction=SYSTEM_PROMPT,
        ),
    )

    raw = (resp.text or "").strip().upper()
    return "ANALYZE" if "ANALYZE" in raw else "CHAT"


def extract_title(raw_text: str) -> str:
    lines = (raw_text or "").strip().splitlines()
    if lines:
        first = lines[0].strip()
        if 3 <= len(first) <= 120:
            return first
    return "موقعیت شغلی"


def extract_requirements(raw_text: str, max_items: int = 6):
    text = raw_text or ""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    items = []
    for l in lines:
        if l.startswith(("•", "-", "*", "–")):
            items.append(l.lstrip("•-*– ").strip())
        if len(items) >= max_items:
            break
    return items


# ======================================================
# 🧠 حافظه: خلاصه‌سازی مرحله‌ای
# ======================================================

def update_chat_summary(chat_id: int, user_id: int | None = None, chunk_limit: int = 18):
    """
    خلاصه را مرحله‌ای آپدیت می‌کند:
    - فقط پیام‌های بعد از last_summarized_message_id را می‌گیرد
    - خلاصه قبلی را به عنوان زمینه می‌دهد
    - بعد از خلاصه‌سازی، last_summarized_message_id را جلو می‌برد
    """
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
        .order_by(Message.message_id.asc())
        .limit(chunk_limit)
        .all()
    )

    if not new_msgs:
        return

    # متن پیام‌های جدید
    new_block = "\n".join(
        [f"{'User' if m.is_user else 'Bot'}: {m.content}" for m in new_msgs]
    )

    previous_summary = (chat.summary or "").strip()

    prompt = f"""
تو باید یک خلاصه‌ی حافظه‌ای کوتاه و دقیق از مکالمه بسازی و همیشه به‌روز نگهش داری.

خلاصه قبلی (اگر وجود دارد):
\"\"\"{previous_summary}\"\"\"

پیام‌های جدید:
\"\"\"{new_block}\"\"\"

قواعد:
- خلاصه نهایی فارسی باشد
- کوتاه اما شامل نکات مهم، اطلاعات شخصی/ترجیحات کاربر، هدف گفتگو، تصمیم‌ها و درخواست‌های کلیدی باشد
- اگر خلاصه قبلی درست است، آن را با پیام‌های جدید ادغام و به‌روز کن
- خروجی فقط خودِ خلاصه باشد
""".strip()

    resp = client.models.generate_content(
        model=CHAT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0,
            max_output_tokens=220,
            system_instruction=SYSTEM_PROMPT,
        ),
    )

    chat.summary = (resp.text or "").strip()
    chat.last_summarized_message_id = new_msgs[-1].message_id
    db.session.commit()


def maybe_update_chat_summary(chat_id: int, user_id: int | None = None, every_n_messages: int = 10):
    """
    هر N پیام یکبار خلاصه را جلو می‌برد.
    """
    q = Chat.query.filter_by(chat_id=chat_id)
    if user_id is not None:
        q = q.filter_by(user_id=user_id)
    chat = q.first()
    if not chat:
        return

    # تعداد کل پیام‌ها
    total = Message.query.filter_by(chat_id=chat_id).count()
    if total % every_n_messages != 0:
        return

    update_chat_summary(chat_id, user_id=user_id)


# ======================================================
# 🧠 تحلیل رزومه
# ======================================================

def analyze_resume(user_text: str):
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

        resume_embedding = get_embedding(user_text, task_type="RETRIEVAL_QUERY")

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

        cards = []
        for idx, job in enumerate(top_jobs, start=1):
            cards.append({
                "job_id": idx,
                "title": extract_title(job.get("text")),
                "company_name": job.get("company") or None,
                "location": None,
                "paycheck": None,
                "requirements": extract_requirements(job.get("text")),
                "match_percent": clamp_percent(job.get("score")),
                "job_url": job.get("url") or None
            })

        yield ("jobs", {"items": cards})

        jobs_text = ""
        for i, job in enumerate(top_jobs, start=1):
            jobs_text += f"""
==============================
🔹 شغل شماره {i}

شرکت: {job['company']}
لینک: {job['url']}
درصد تطابق: {job['score'] * 100:.1f}٪

[متن آگهی]
{job['text']}
"""

        prompt = f"""
بر اساس رزومه کاربر، ۳ موقعیت شغلی با بیشترین تطابق انتخاب شده‌اند.

[رزومه کاربر]
{user_text}

[۳ آگهی منتخب]
{jobs_text}

گزارش حرفه‌ای شامل:
1) خلاصه هر آگهی
2) ارزیابی تطابق رزومه با هر شغل
3) مقایسه نهایی بین ۳ شغل
4) پیشنهاد بهترین گزینه برای اقدام به همراه دلیل
""".strip()

        stream = client.models.generate_content_stream(
            model=CHAT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=Config.GEMINI_TEMPERATURE,
                max_output_tokens=Config.GEMINI_MAX_OUTPUT_TOKENS,
                system_instruction=SYSTEM_PROMPT,
            ),
        )

        for chunk in stream:
            if chunk.text:
                yield chunk.text

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
# 🤖 تولید پاسخ بات (با حافظه + خلاصه)
# ======================================================

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
        for item in analyze_resume(user_text):
            if isinstance(item, tuple) and len(item) == 2:
                yield item[0], item[1]
            else:
                yield "content", item
        return

    contents = []

    # خلاصه مکالمات قبلی (حافظه بلندمدت)
    if chat.summary:
        contents.append({
            "role": "user",
            "parts": [{"text": f"خلاصه مکالمات قبلی: {chat.summary}"}]
        })

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
        contents.append({
            "role": "user" if msg.is_user else "model",
            "parts": [{"text": msg.content}]
        })

    # پیام جدید
    contents.append({"role": "user", "parts": [{"text": user_text}]})

    stream = client.models.generate_content_stream(
        model=CHAT_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            temperature=Config.GEMINI_TEMPERATURE,
            max_output_tokens=Config.GEMINI_MAX_OUTPUT_TOKENS,
            system_instruction=SYSTEM_PROMPT,
        ),
    )

    for chunk in stream:
        if chunk.text:
            yield "content", chunk.text
