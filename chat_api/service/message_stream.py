from datetime import datetime, timezone

from chat_api.models import Message
from chat_api.models.job_card import JobCard
from ..extensions import db

from ..utils.message_utils import sse
from ..utils.chat_utils import chat_brief
from .botMessage import generate_bot_reply
from .memory_summary import maybe_update_chat_summary


def stream_bot_reply(chat, user_msg, user_text: str, user_id: int, title_changed: bool):
    """
    SSE generator
    - meta
    - jobs
    - content
    - done
    - error
    """
    full_text = ""
    pending_cards = None  # کارت‌ها را موقتاً نگه می‌داریم

    try:
        reply_gen = generate_bot_reply(chat.chat_id, user_text, user_id=user_id)

        try:
            first = next(reply_gen)
        except StopIteration:
            yield sse("error", {"message": "empty response from bot"})
            return

        if not isinstance(first, tuple) or len(first) != 2:
            yield sse("error", {"message": "protocol error: invalid first yield"})
            return

        tag, intent_type = first
        if tag != "intent":
            yield sse("error", {"message": "protocol error: first yield must be intent"})
            return

        yield sse("meta", {
            "chat": chat_brief(chat),
            "user_message_id": user_msg.message_id,
            "type": intent_type,
            "title_changed": title_changed,
        })

        for item in reply_gen:
            if not isinstance(item, tuple) or len(item) != 2:
                continue

            tag, chunk = item

            if tag == "jobs" and chunk:
                pending_cards = chunk.get("items")
                yield sse("jobs", chunk)
            elif tag == "content" and chunk:
                full_text += chunk
                yield sse("content", {"delta": chunk})

        if not full_text.strip():
            yield sse("error", {"message": "empty bot content"})
            return

        bot_msg = Message(
            chat_id=chat.chat_id,
            content=full_text.strip(),
            role="assistant",
        )
        db.session.add(bot_msg)

        if hasattr(chat, "updated_at"):
            chat.updated_at = datetime.now(timezone.utc)

        db.session.flush()  # bot_msg.message_id را بگیریم

        # ذخیره کارت‌ها در DB لینک به پیام bot
        if pending_cards:
            job_card = JobCard(
                message_id=bot_msg.message_id,
                cards_json=pending_cards,
            )
            db.session.add(job_card)

        db.session.commit()

        try:
            maybe_update_chat_summary(chat.chat_id, user_id=user_id, every_n_messages=10)
        except Exception:
            pass

        yield sse("done", {"bot_message_id": bot_msg.message_id})

    except Exception as e:
        db.session.rollback()
        yield sse("error", {"message": str(e)})