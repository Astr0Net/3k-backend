from chat_api.models import Message
from ..extensions import db

from .message_helpers import sse, chat_brief
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

    try:
        reply_gen = generate_bot_reply(chat.chat_id, user_text, user_id=user_id)

        # اولین yield باید intent باشد
        try:
            first = next(reply_gen)
        except StopIteration:
            yield sse("error", {"message": "empty response from bot"})
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

        for tag, chunk in reply_gen:
            if tag == "jobs" and chunk:
                yield sse("jobs", chunk)
            elif tag == "content" and chunk:
                full_text += chunk
                yield sse("content", {"delta": chunk})

        # ذخیره پیام بات
        bot_msg = Message(
            chat_id=chat.chat_id,
            content=full_text,
            time=Message.now_as_string(),
            is_user=False,
        )
        db.session.add(bot_msg)
        db.session.commit()

        # خلاصه‌سازی (اختیاری)
        try:
            maybe_update_chat_summary(chat.chat_id, user_id=user_id, every_n_messages=10)
        except Exception:
            pass

        yield sse("done", {"bot_message_id": bot_msg.message_id})

    except Exception as e:
        db.session.rollback()
        yield sse("error", {"message": str(e)})