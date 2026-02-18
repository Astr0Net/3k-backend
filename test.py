import sys
# تنظیم انکودینگ برای نمایش درست فارسی در ویندوز
sys.stdout.reconfigure(encoding='utf-8')

from google import genai
from google.genai import types

# --- کلید خود را اینجا بگذارید ---
API_KEY = "AIzaSyBokVQZDSot7mseLJexJBhNsXz22J7yrdI" 

client = genai.Client(api_key=API_KEY)

text = "هوش مصنوعی جمنای بسیار قدرتمند است."

print(f"در حال دریافت امبدینگ برای متن: '{text}' ...\n")

try:
    # استفاده از دقیقاً همان نام مدلی که در لیست پیدا کردیم
    response = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            title="Embedding Test"
        )
    )

    # استخراج بردار
    # در این مدل خاص، خروجی معمولاً در embeddings[0].values قرار دارد
    if response.embeddings:
        vector = response.embeddings[0].values
        print("✅ عملیات موفقیت آمیز بود!")
        print(f"طول بردار (تعداد ابعاد): {len(vector)}")
        print(f"۵ عدد اول بردار: {vector[:5]}")
    else:
        print("❌ خروجی خالی بود.")

except Exception as e:
    print(f"❌ خطا: {e}")