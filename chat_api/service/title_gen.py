from .qom_llm import qom_chat

TITLE_SYSTEM = """
You are a title generator for a Persian job-search chatbot.
Rules:
- Output ONLY the title. Nothing else.
- Language: Persian (Farsi) only.
- Length: 2 to 4 words maximum.
- No punctuation, no quotes, no explanation.
- Capture the main topic of the user's message.
""".strip()

TITLE_PROMPT_TEMPLATE = """
پیام کاربر:
\"\"\"
{user_text}
\"\"\"

یک عنوان کوتاه فارسی (۲ تا ۴ کلمه) برای این مکالمه بساز.
فقط عنوان را بنویس.
""".strip()


def generate_chat_title(first_user_message: str) -> str:
    text = (first_user_message or "").strip()
    if not text:
        return "گفتگوی جدید"

    prompt = TITLE_PROMPT_TEMPLATE.format(user_text=text[:500])

    try:
        out = qom_chat(
            [
                {"role": "system", "content": TITLE_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=15,
        )
        out = (out or "").replace('"', '').replace("'", "").strip()

        # اگر خروجی انگلیسی یا خالی بود
        if not out or out.isascii():
            return "گفتگوی جدید"

        return out[:60]
    except Exception:
        return "گفتگوی جدید"