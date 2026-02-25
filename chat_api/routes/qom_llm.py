import requests
from config import Config


def chunk_text(text: str, chunk_size: int = 220):
    """برای SSE: چون stream واقعی نداریم، خروجی را تکه‌ای می‌کنیم."""
    text = text or ""
    if not text:
        return
    for i in range(0, len(text), chunk_size):
        yield text[i:i + chunk_size]


def qom_chat(messages, temperature=None, max_tokens=None, timeout=None) -> str:
    """Call Qom LLM Chat Completions."""
    if not Config.LLM_API_KEY:
        raise RuntimeError("LLM_API_KEY is not set")

    url = Config.llm_chat_url()
    headers = {
        "Authorization": f"Bearer {Config.LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": Config.LLM_MODEL,
        "messages": messages,
        "temperature": Config.LLM_TEMPERATURE if temperature is None else temperature,
        "max_tokens": Config.LLM_MAX_TOKENS if max_tokens is None else max_tokens,
    }

    r = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=Config.LLM_TIMEOUT if timeout is None else timeout,
    )
    r.raise_for_status()
    data = r.json()
    return (data["choices"][0]["message"]["content"] or "").strip()