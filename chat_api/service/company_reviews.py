import json


def clean_company_name(name: str) -> str:
    return (name or "").strip()


def fetch_company_reviews(cursor, company_names: list[str]) -> dict:
    """
    از جدول companies نظرات را می‌خواند.
    خروجی: dict[company_name] = reviews(json)
    """
    names = [n for n in (clean_company_name(x) for x in company_names) if n]
    if not names:
        return {}

    reviews_map: dict[str, object] = {}

    # exact match
    try:
        cursor.execute(
            """
            SELECT company_name, reviews
            FROM companies
            WHERE company_name = ANY(%s);
            """,
            (names,),
        )
        for cn, rv in cursor.fetchall():
            reviews_map[clean_company_name(cn)] = rv
    except Exception:
        return reviews_map

    # soft match for missing
    missing = [n for n in names if n not in reviews_map]
    for n in missing:
        try:
            cursor.execute(
                """
                SELECT company_name, reviews
                FROM companies
                WHERE company_name ILIKE %s
                LIMIT 1;
                """,
                (n,),
            )
            row = cursor.fetchone()
            if row:
                _, rv = row
                reviews_map[clean_company_name(n)] = rv
        except Exception:
            pass

    return reviews_map


def format_reviews_for_prompt(reviews, max_items: int = 6) -> str:
    """
    reviews ممکنه list/dict/str/None باشه.
    خروجی: متن کوتاه برای prompt
    """
    if reviews is None:
        return ""

    if isinstance(reviews, str) and reviews.strip():
        try:
            reviews = json.loads(reviews)
        except Exception:
            return reviews.strip()[:1200]

    if isinstance(reviews, list):
        items = []
        for x in reviews:
            s = str(x).strip()
            if s:
                items.append(s)
            if len(items) >= max_items:
                break
        return ("\n".join([f"- {it}" for it in items])).strip()[:1500]

    if isinstance(reviews, dict):
        try:
            return json.dumps(reviews, ensure_ascii=False)[:1500]
        except Exception:
            return str(reviews)[:1500]

    return str(reviews).strip()[:1500]