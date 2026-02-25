import numpy as np
import requests
from config import Config


def get_embedding(text: str, task_type: str | None = None):
    """
    Embedding (bge-m3)
    task_type فقط برای سازگاری امضا نگه داشته شده.
    """
    text = (text or "").strip()
    if not text:
        return np.zeros((Config.EMBED_EXPECTED_DIM,), dtype=float)

    payload = {
        "model": Config.EMBED_MODEL,
        "input": [text[:4000]],
        "encoding_format": "float"
    }

    r = requests.post(
        f"{(Config.EMBED_BASE_URL or '').rstrip('/')}/v1/embeddings",
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=Config.EMBED_TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()

    vec = data["data"][0]["embedding"]
    arr = np.array(vec, dtype=float)

    # نرمال‌سازی ابعاد
    if arr.size != Config.EMBED_EXPECTED_DIM:
        if arr.size < Config.EMBED_EXPECTED_DIM:
            padded = np.zeros((Config.EMBED_EXPECTED_DIM,), dtype=float)
            padded[:arr.size] = arr
            arr = padded
        else:
            arr = arr[:Config.EMBED_EXPECTED_DIM]

    return arr


def cosine_similarity(a, b) -> float:
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def clamp_percent(score: float) -> int:
    try:
        p = int(round(float(score) * 100))
    except Exception:
        p = 0
    return max(0, min(100, p))