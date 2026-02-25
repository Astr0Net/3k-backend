import requests

# =========================
# تنظیمات
# =========================

LLM_URL = "https://llm-test.ssl.qom.ac.ir/llm/v1/chat/completions"
LLM_API_KEY = "d72d2ecab7e0325aa710f5b784df2155"
LLM_MODEL = "CoreStableLLM"


def test_llm():
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": "تو یک دستیار فارسی هستی."},
            {"role": "user", "content": "سلام، خودت را معرفی کن."}
        ],
        "temperature": 0.6,
        "max_tokens": 512
    }

    print("🚀 Sending request to Qom LLM...")

    try:
        response = requests.post(LLM_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        data = response.json()

        print("\n✅ Raw Response JSON:")
        print(data)

        print("\n🤖 Assistant Response:")
        print(data["choices"][0]["message"]["content"])

    except requests.exceptions.HTTPError as e:
        print("\n❌ HTTP Error:")
        print(response.status_code, response.text)

    except Exception as e:
        print("\n❌ Error:")
        print(str(e))


if __name__ == "__main__":
    test_llm()