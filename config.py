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
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_MINUTES", "15"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_REFRESH_DAYS", "30"))
    )

    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # =========================
    # Gemini API
    # =========================
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # =========================
    # Gemini Models
    # =========================
    GEMINI_CHAT_MODEL = os.getenv(
        "GEMINI_CHAT_MODEL",
        "models/gemini-2.0-flash"
    )

    GEMINI_EMBEDDING_MODEL = os.getenv(
        "GEMINI_EMBEDDING_MODEL",
        "models/gemini-embedding-001"
    )

    # =========================
    # Gemini Generation Settings
    # =========================
    GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.6"))
    GEMINI_MAX_OUTPUT_TOKENS = int(
        os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "1024")
    )
