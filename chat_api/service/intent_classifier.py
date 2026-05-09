import json
from .qom_llm import qom_chat

INTENT_SYSTEM_PROMPT = "You are a strict intent classifier. Return ONLY valid JSON. No extra text. No markdown."

def detect_intent(user_text: str) -> str:
    """
    خروجی: 'ANALYZE' یا 'CHAT'
    """
    user_text = (user_text or "").strip()

    prompt = f"""
Return ONLY valid JSON with this schema:
{{
  "intent": "ANALYZE" | "CHAT",
  "confidence": 0.0,
  "reason": "short"
}}

Rules:
- If user provides resume/CV, skills list, or asks job recommendations: ANALYZE
- Otherwise: CHAT

User text:
\"\"\"{user_text}\"\"\"
""".strip()

    try:
        raw = qom_chat(
            [
                {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=160
        )
    except Exception:
        return "ANALYZE" if len(user_text) >= 120 else "CHAT"

    try:
        obj = json.loads(raw)
        intent = (obj.get("intent") or "").strip().upper()
        conf = float(obj.get("confidence") or 0.0)
    except Exception:
        return "ANALYZE" if len(user_text) >= 120 else "CHAT"

    if intent not in ("ANALYZE", "CHAT"):
        return "ANALYZE" if len(user_text) >= 120 else "CHAT"

    if conf < 0.55 and len(user_text) >= 120:
        return "ANALYZE"

    return intent