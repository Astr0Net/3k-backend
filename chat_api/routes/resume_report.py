from .qom_llm import qom_chat, chunk_text
from .embeddings import get_embedding
from .company_reviews import fetch_company_reviews
from .job_scoring import open_conn, load_jobs_with_embeddings, score_jobs, build_cards, build_jobs_text_for_prompt


SYSTEM_PROMPT = """
شما یک «دستیار کاریابی» و تحلیل‌گر منابع انسانی حرفه‌ای هستید.

قوانین:
- پاسخ‌ها رسمی، دقیق و حمایتی باشند
- فقط بر اساس داده‌های ارائه‌شده پاسخ بده
- از حدس، اغراق و اطلاعات ساختگی خودداری کن
- زبان پاسخ‌ها فارسی باشد
- اگر کاربر درباره هویت/نام/مدل پرسید، فقط بگو: «من یک دستیار کاریابی هستم.»
""".strip()


def analyze_resume_stream(user_text: str):
    conn = None
    cursor = None

    try:
        conn = open_conn()
        cursor = conn.cursor()

        rows = load_jobs_with_embeddings(cursor)
        if not rows:
            yield "❌ هیچ آگهی شغلی برای مقایسه یافت نشد."
            return

        resume_embedding = get_embedding(user_text, task_type="RETRIEVAL_QUERY")
        scored = score_jobs(rows, resume_embedding)
        top_jobs = scored[:3]

        # reviews
        top_companies = [j.get("company_name") for j in top_jobs if j.get("company_name")]
        reviews_map = fetch_company_reviews(cursor, top_companies)

        # cards
        cards = build_cards(top_jobs, reviews_map)
        yield "✅ ۳ آگهی پیشنهادی از دیتابیس پیدا شد. در حال آماده‌سازی گزارش..."
        yield ("jobs", {"items": cards})

        # report
        jobs_text = build_jobs_text_for_prompt(top_jobs, reviews_map)
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
5) اگر «نظرات درباره شرکت» وجود داشت، در تصمیم‌گیری و ریسک‌ها/مزایا لحاظ کن
""".strip()

        report = qom_chat(
            [{"role": "system", "content": SYSTEM_PROMPT},
             {"role": "user", "content": prompt}],
        )

        for part in chunk_text(report, chunk_size=220):
            yield part

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