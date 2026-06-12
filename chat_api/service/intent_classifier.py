import json
from .qom_llm import qom_chat

INTENT_SYSTEM_PROMPT = """
You are a strict intent classifier for a job-search assistant app.
Output ONLY valid JSON. No markdown. No explanation. No extra text.
""".strip()

INTENT_USER_TEMPLATE = """
Classify the user's message into exactly one intent.

## Intent Definitions:
- ANALYZE: User provides resume content, CV, skills list, work experience, OR explicitly asks for job recommendations/matching based on their background.
- CHAT: General questions about careers, interview tips, salary, market trends, or anything else.

## Rules:
- If the message contains personal work history, education, or skills list → ANALYZE
- If the message is a question or general discussion → CHAT
- Short messages (under 80 chars) with no personal info → almost always CHAT

## Output schema (strict):
{{
  "intent": "ANALYZE" or "CHAT",
  "confidence": float between 0.0 and 1.0,
  "reason": "one short sentence in English"
}}

## User message:
\"\"\"
{user_text}
\"\"\"
""".strip()


def _fallback_intent(user_text: str) -> str:
    """
    Heuristic fallback وقتی LLM جواب نداد.
    بر اساس کلمات کلیدی، نه فقط طول متن.
    """
    text_lower = user_text.lower()

    resume_keywords = [
        "رزومه", "سابقه کار", "مهارت", "تجربه", "فارغ‌التحصیل",
        "دانشگاه", "کارشناسی", "لیسانس", "فوق لیسانس", "دکترا",
        "سال تجربه", "پروژه", "زبان برنامه‌نویسی", "python", "java",
        "javascript", "react", "backend", "frontend", "devops",
        "بک اند", "فرانت اند", "برنامه نویس"
    ]

    hit = sum(1 for kw in resume_keywords if kw in text_lower)

    if hit >= 2 or (hit >= 1 and len(user_text) >= 150):
        return "ANALYZE"
    return "CHAT"


def detect_intent(user_text: str) -> str:
    """
    خروجی: 'ANALYZE' یا 'CHAT'
    """
    user_text = (user_text or "").strip()
    if not user_text:
        return "CHAT"

    prompt = INTENT_USER_TEMPLATE.format(user_text=user_text[:1500])

    try:
        raw = qom_chat(
            [
                {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=120,
        )
    except Exception:
        return _fallback_intent(user_text)

    try:
        raw_clean = raw.strip().strip("```json").strip("```").strip()
        obj = json.loads(raw_clean)
        intent = (obj.get("intent") or "").strip().upper()
        conf = float(obj.get("confidence") or 0.0)
    except Exception:
        return _fallback_intent(user_text)

    if intent not in ("ANALYZE", "CHAT"):
        return _fallback_intent(user_text)

    # اگر confidence پایین است، fallback heuristic تصمیم می‌گیرد
    if conf < 0.60:
        return _fallback_intent(user_text)

    return intent