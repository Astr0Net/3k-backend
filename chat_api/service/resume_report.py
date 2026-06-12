from .qom_llm import qom_chat, chunk_text
from .embeddings import get_embedding
from .company_reviews import fetch_company_reviews
from .job_scoring import open_conn, load_jobs_with_embeddings, score_jobs, build_cards, build_jobs_text_for_prompt


RESUME_ANALYSIS_SYSTEM = """
شما «دستیار کاریابی» هستید — تحلیل‌گر حرفه‌ای رزومه و بازار کار ایران.

## هویت
- اگر کاربر درباره هویت پرسید: «من دستیار کاریابی شما هستم.»

## قوانین تحلیل
- فقط بر اساس داده‌های ارائه‌شده تحلیل کن — هیچ اطلاعاتی جعل نکن
- اگر اطلاعات کافی نیست، صادقانه بگو
- زبان: فارسی حرفه‌ای و حمایتی
- از اغراق و تعریف‌های کلیشه‌ای خودداری کن
""".strip()


REPORT_PROMPT_TEMPLATE = """
بر اساس رزومه کاربر و ۳ آگهی شغلی زیر، یک گزارش تحلیلی دقیق بنویس.

[رزومه کاربر]
{resume}

[۳ آگهی منتخب با بیشترین تطابق]
{jobs}

---

## ساختار گزارش (دقیقاً همین ترتیب را رعایت کن):

### ۱. خلاصه سریع هر شغل
برای هر شغل یک پاراگراف کوتاه: عنوان، شرکت، مهارت‌های کلیدی موردنیاز.

### ۲. تحلیل تطابق رزومه با هر شغل
برای هر شغل:
- ✅ مهارت‌هایی که داری و با شغل match می‌کند
- ❌ گپ‌های مهارتی (چه چیزی کم داری)
- درصد تطابق کلی (همان مقداری که سیستم محاسبه کرده)

### ۳. مقایسه نهایی ۳ شغل
یک مقایسه کوتاه: کدام شغل برای چه پروفایلی مناسب‌تر است.

### ۴. پیشنهاد بهترین گزینه
یک شغل را به عنوان اولویت اول پیشنهاد بده + دلیل مشخص (نه کلیشه‌ای).

### ۵. اقدام بعدی
۲-۳ قدم عملی مشخص که کاربر باید همین هفته انجام دهد.

{company_reviews_note}
""".strip()


def analyze_resume_stream(user_text: str):
    conn = None
    cursor = None

    try:
        conn = open_conn()
        cursor = conn.cursor()

        rows = load_jobs_with_embeddings(cursor)
        if not rows:
            yield "❌ هیچ آگهی شغلی در دیتابیس یافت نشد."
            return

        resume_embedding = get_embedding(user_text, task_type="RETRIEVAL_QUERY")
        scored = score_jobs(rows, resume_embedding)
        top_jobs = scored[:3]

        top_companies = [j.get("company_name") for j in top_jobs if j.get("company_name")]
        reviews_map = fetch_company_reviews(cursor, top_companies)

        cards = build_cards(top_jobs, reviews_map)
        yield "✅ ۳ آگهی پیشنهادی از دیتابیس پیدا شد. در حال آماده‌سازی گزارش..."
        yield ("jobs", {"items": cards})

        jobs_text = build_jobs_text_for_prompt(top_jobs, reviews_map)

        has_reviews = any(reviews_map.get(j.get("company_name")) for j in top_jobs)
        company_reviews_note = (
            "### نکته درباره شرکت‌ها\n"
            "اطلاعات نظرات کارمندان برای برخی شرکت‌ها موجود است. "
            "در پیشنهاد نهایی، ریسک‌ها و مزایای فرهنگ سازمانی را هم لحاظ کن."
            if has_reviews else ""
        )

        prompt = REPORT_PROMPT_TEMPLATE.format(
            resume=user_text,
            jobs=jobs_text,
            company_reviews_note=company_reviews_note,
        )

        report = qom_chat(
            [
                {"role": "system", "content": RESUME_ANALYSIS_SYSTEM},
                {"role": "user", "content": prompt},
            ],
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