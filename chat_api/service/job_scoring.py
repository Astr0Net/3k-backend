import psycopg2
from pgvector.psycopg2 import register_vector
from config import Config

from .embeddings import get_embedding, cosine_similarity, clamp_percent
from ..utils.requirements_utils import normalize_requirements
from .company_reviews import clean_company_name, format_reviews_for_prompt


def load_jobs_with_embeddings(cursor):
    cursor.execute("""
        SELECT
            job_id,
            job_url,
            source_site,
            job_title,
            company_name,
            location,
            paycheck,
            requirements,
            raw_text,
            embedding
        FROM jobs
        WHERE embedding IS NOT NULL;
    """)
    return cursor.fetchall()


def score_jobs(rows, resume_embedding):
    scored = []
    for (
        job_id, job_url, source_site, job_title, company_name,
        location, paycheck, requirements, raw_text, embedding
    ) in rows:
        try:
            score = cosine_similarity(resume_embedding, embedding)
        except Exception:
            score = 0.0

        scored.append({
            "job_id": job_id,
            "job_url": job_url,
            "source_site": source_site,
            "job_title": job_title,
            "company_name": company_name,
            "location": location,
            "paycheck": paycheck,
            "requirements": requirements,
            "raw_text": raw_text,
            "score": score,
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def build_cards(top_jobs, reviews_map, max_req_items: int = 6):
    cards = []
    for job in top_jobs:
        req_list = normalize_requirements(job.get("requirements"), job.get("raw_text") or "", max_items=max_req_items)
        cn = clean_company_name(job.get("company_name"))
        cards.append({
            "title": job.get("job_title"),
            "company_name": job.get("company_name"),
            "location": job.get("location"),
            "paycheck": job.get("paycheck"),
            "requirements": req_list,
            "match_percent": clamp_percent(job.get("score", 0.0)),
            "job_url": job.get("job_url"),
            "source_site": job.get("source_site"),
            "company_reviews": reviews_map.get(cn),
        })
    return cards


def build_jobs_text_for_prompt(top_jobs, reviews_map) -> str:
    out = ""
    for i, job in enumerate(top_jobs, start=1):
        cn = clean_company_name(job.get("company_name"))
        rv = reviews_map.get(cn)
        reviews_text = format_reviews_for_prompt(rv)
        reviews_block = f"\n\n[نظرات درباره شرکت]\n{reviews_text}\n" if reviews_text else ""

        out += f"""
==============================
🔹 شغل شماره {i}

عنوان: {job.get('job_title') or '-'}
شرکت: {job.get('company_name') or '-'}
مکان: {job.get('location') or '-'}
حقوق: {job.get('paycheck') or '-'}
لینک: {job.get('job_url') or '-'}
منبع: {job.get('source_site') or '-'}
درصد تطابق: {job.get('score', 0.0) * 100:.1f}٪
{reviews_block}
[متن کامل آگهی]
{job.get('raw_text') or ''}
"""
    return out.strip()


def open_conn():
    conn = psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI, connect_timeout=8)
    register_vector(conn)
    return conn