# test_db_connection.py
import os
import psycopg2
from dotenv import load_dotenv

# 1. اطمینان از لود شدن .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# 2. بررسی وجود متغیر قبل از اتصال
if not DATABASE_URL:
    print("❌ خطا: متغیر SQLALCHEMY_DATABASE_URI در فایل .env پیدا نشد!")
    print("📍 لطفاً بررسی کنید:")
    print("   - فایل .env در کنار app.py قرار دارد؟")
    print("   - نام کلید دقیقاً SQLALCHEMY_DATABASE_URI است؟")
    print("   - پکیج python-dotenv نصب است؟ (pip install python-dotenv)")
    exit(1)

print(f"🔗 در حال اتصال به دیتابیس...")

try:
    # connect_timeout=5 جلوگیری از هنگ کردن بی‌نهایت
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
    cur = conn.cursor()
    cur.execute("SELECT version();")
    print("✅ اتصال موفقیت‌آمیز بود!")
    print(f"📦 نسخه PostgreSQL: {cur.fetchone()[0]}")
    cur.close()
    conn.close()
except psycopg2.OperationalError as e:
    print(f"❌ خطای اتصال به دیتابیس: {e}")
except Exception as e:
    print(f"❌ خطای غیرمنتظره: {e}")  