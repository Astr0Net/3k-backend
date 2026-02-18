import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    # =========================
    # Flask
    # =========================
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

    # =========================
    # Database
    # =========================
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # =========================
    # JWT
    # =========================
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)  # پیشنهاد: جداگانه ست کن
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "15")))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "30")))

    # اگر می‌خوای توکن‌ها در Header باشن (پیشنهاد برای API + React):
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # =========================
    # Liara AI - Embedding
    # =========================
    LIARA_EMBEDDING_API_KEY = os.getenv("LIARA_EMBEDDING_API_KEY")
    LIARA_EMBEDDING_BASE_URL = os.getenv("LIARA_EMBEDDING_BASE_URL")

    # =========================
    # Liara AI - Chat
    # =========================
    LIARA_CHAT_API_KEY = os.getenv("LIARA_CHAT_API_KEY")
    LIARA_CHAT_BASE_URL = os.getenv("LIARA_CHAT_BASE_URL")

    # =========================
    # Models
    # =========================
    EMBEDDING_MODEL = "openai/text-embedding-3-small"
    GPT_MODEL = "openai/gpt-5-nano"
