from .qom_llm import qom_chat

TITLE_SYSTEM = "شما یک تولیدکننده عنوان هستید. خروجی فقط عنوان باشد."

def generate_chat_title(first_user_message: str) -> str:
    """
    عنوان خیلی کوتاه فارسی (حداکثر ۳ کلمه)
    """
    text = (first_user_message or "").strip()
    if not text:
        return "چت جدید"

    prompt = (
        "بر اساس پیام زیر، یک عنوان بسیار کوتاه فارسی (حداکثر ۳ کلمه) بساز. "
        "فقط خود عنوان را برگردان:\n\n"
        f"{text}"
    )

    try:
        out = qom_chat(
            [
                {"role": "system", "content": TITLE_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=20,
        )
        out = (out or "").replace('"', '').strip()
        return out[:60] if out else "چت جدید"
    except Exception:
        return "چت جدید"