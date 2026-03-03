import json
import time
import requests
from config import Config


def clean_prefix(text: str) -> str:
    """
    هرچی قبل از شروع جواب واقعی است را حذف می‌کند.
    اینجا فرض کردیم جواب با 'استریم API' شروع می‌شود.
    اگر خواستی عمومی‌ترش کنیم، می‌گم چطور.
    """
    if not text:
        return text
    anchor = "استریم API"
    idx = text.find(anchor)
    return text[idx:] if idx != -1 else text


def stream_chat_clean(idle_seconds: float = 2.5):
    url = Config.llm_chat_url()
    headers = {
        "Authorization": f"Bearer {Config.LLM_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    payload = {
        "model": Config.LLM_MODEL,
        "messages": [
            {"role": "system", "content": "پاسخ را فارسی بده و فقط پاسخ نهایی را بده. هیچ توضیح اضافه یا تحلیل ننویس."},
            {"role": "user", "content": """این متن رو  یک طرف تراکت نوشتم برای اون طرف دیگه پیشنهادی داری؟؟ پیتزا فروشیه 
             ممنون از خرید تون
لطفا توی اسنپ فود برامون کامنت بزارید 
و پنج ستاره بدین
اگر تلفنی سفارش بدین غذا زود تر و گرم تر خدمت
تون ارسال خواهد شد
به زودی سایت ثبت سفارش هم درست میکنیم"""},
        ],
        "temperature": Config.LLM_TEMPERATURE,
        "max_tokens": Config.LLM_MAX_TOKENS,
        "stream": True,
    }

    timeout = (10, 60)

    with requests.post(url, headers=headers, json=payload, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        print("Status:", r.status_code)
        print("Content-Type:", r.headers.get("Content-Type"))

        last_ts = time.time()
        buf = []

        for raw_line in r.iter_lines(decode_unicode=True):
            if time.time() - last_ts > idle_seconds:
                break
            if not raw_line:
                continue

            line = raw_line.strip()
            if not line.startswith("data:"):
                continue

            data_part = line[len("data:"):].strip()
            if not data_part:
                continue

            last_ts = time.time()

            if data_part in ("[DONE]", "DONE"):
                break

            obj = json.loads(data_part)
            choice = (obj.get("choices") or [{}])[0]
            delta = choice.get("delta") or {}

            chunk = delta.get("content") or delta.get("reasoning_content") or ""
            if chunk:
                buf.append(chunk)

            if choice.get("finish_reason"):
                break

        full = "".join(buf)
        cleaned = clean_prefix(full)

        print("\n--- CLEAN OUTPUT ---\n")
        print(cleaned)


if __name__ == "__main__":
    stream_chat_clean()