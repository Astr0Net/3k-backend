import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # =========================
    # Flask
    # =========================
    SECRET_KEY = os.getenv("SECRET_KEY")

    # =========================
    # Database
    # =========================
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

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
