import os
from datetime import timedelta
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
    # JWT
    # =========================
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_MINUTES"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_REFRESH_DAYS"))
    )

    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # =========================
    # Chat LLM (Qom)
    # =========================
    LLM_BASE_URL = os.getenv("LLM_BASE_URL")
    LLM_CHAT_ENDPOINT = os.getenv("LLM_CHAT_ENDPOINT")
    LLM_API_KEY = os.getenv("LLM_API_KEY") 
    LLM_MODEL = os.getenv("LLM_MODEL")

    # Generation settings
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS"))
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT"))

    @classmethod
    def llm_chat_url(cls) -> str:
        """
        Full URL for chat completions endpoint.
        Example: https://llm-test.ssl.qom.ac.ir/llm/v1/chat/completions
        """
        base = (cls.LLM_BASE_URL or "").rstrip("/")
        endpoint = (cls.LLM_CHAT_ENDPOINT or "").strip()
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        return base + endpoint

    # =========================
    # Embedding (Qom)
    # =========================
    EMBED_BASE_URL = os.getenv("EMBED_BASE_URL")
    EMBED_MODEL = os.getenv("EMBED_MODEL")
    EMBED_EXPECTED_DIM = int(os.getenv("EMBED_EXPECTED_DIM"))
    EMBED_TIMEOUT = int(os.getenv("EMBED_TIMEOUT"))