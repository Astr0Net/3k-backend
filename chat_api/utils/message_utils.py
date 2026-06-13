import json
from chat_api.models import Message


def message_dto(m: Message) -> dict:
    return {
        "message_id": m.message_id,
        "content": m.content,
        "created_at": m.created_at.isoformat() if m.created_at else None,
        "role": m.role,
        "job_cards": None,  # توسط message_dto_list پر می‌شود
    }


def sse(event: str, payload: dict):
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"