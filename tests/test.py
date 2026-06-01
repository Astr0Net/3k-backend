# test_final.py
import requests
from config import Config

def chat_test():
    r = requests.post(
        Config.llm_chat_url(),
        headers={
            "Authorization": f"Bearer {Config.LLM_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": Config.LLM_MODEL,
            "messages": [
                {"role": "system", "content": "فقط و فقط به فارسی پاسخ بده. بدون توضیح اضافه."},
                {"role": "user", "content": "سلام، فقط بنویس: متصل شد."}
            ],
            "max_tokens": 500
        },
        timeout=(10, 30)
    )
    r.raise_for_status()
    msg = r.json()["choices"][0]["message"]
    # پشتیبانی از هر دو فیلد content و reasoning
    print((msg.get("content") or msg.get("reasoning") or "").strip())

if __name__ == "__main__":
    chat_test()