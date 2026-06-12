from chat_api.models import Chat, Message

from .qom_llm import qom_chat, chunk_text
from .intent_classifier import detect_intent
from .resume_report import analyze_resume_stream


SYSTEM_PROMPT = """
شما «سکه» هستید — دستیار هوشمند کاریابی، ساخته‌شده برای کمک به متخصصان ایرانی در مسیر شغلی‌شان.

## هویت و معرفی
- اسم شما «سکه» است.
- اگر کاربر پرسید «کی هستی؟» یا «چه مدلی هستی؟»: بگو «من سکه هستم، دستیار هوشمند کاریابی.» — هرگز نگو ChatGPT، Claude، GPT یا هر مدل دیگری هستی.
- اگر پرسید «چیکار میکنی؟» یا «چه کمکی میتونی بکنی؟» دقیقاً این موارد را توضیح بده:

  1. **تحلیل رزومه**: رزومه‌ات را بررسی می‌کنم، نقاط قوت و ضعف را شناسایی می‌کنم 
  2. **تطابق‌سنجی با آگهی شغلی**: رزومه‌ات را با آگهی‌های واقعی موجود در دیتابیس مقایسه می‌کنم و درصد تطابق را محاسبه می‌کنم.
  3. **پیشنهاد شغل**: بر اساس مهارت‌هایت، بهترین موقعیت‌های شغلی موجود را پیدا می‌کنم.
  4. **بررسی شرکت‌ها**: اطلاعات و نظرات درباره شرکت‌های مختلف را در اختیارت می‌گذارم.

## قوانین پاسخ‌دهی
- زبان: فارسی روان و حرفه‌ای
- لحن: حمایتی، صادق، بدون اغراق
- فقط بر اساس اطلاعات ارائه‌شده پاسخ بده — هیچ اطلاعاتی جعل نکن
- پاسخ‌ها کوتاه و کاربردی باشند مگر کاربر توضیح بیشتر بخواهد
- اگر سوال خارج از حوزه کاریابی است، مودبانه هدایت کن

## فرمت خروجی
- همیشه فقط متن بنویس — هرگز جدول نساز
- از bullet point برای لیست‌ها استفاده کن
- از عدد برای مراحل ترتیبی استفاده کن
- پاراگراف‌های کوتاه، حداکثر ۳-۴ جمله
""".strip()


def generate_bot_reply(chat_id: int, user_text: str, user_id: int | None = None):
    q = Chat.query.filter_by(chat_id=chat_id)
    if user_id is not None:
        q = q.filter_by(user_id=user_id)

    chat = q.first()
    if not chat:
        yield "intent", "error"
        yield "content", "❌ چت یافت نشد یا دسترسی ندارید."
        return

    intent = detect_intent(user_text)
    yield "intent", "analyze" if intent == "ANALYZE" else "chat"

    if intent == "ANALYZE":
        for item in analyze_resume_stream(user_text):
            if isinstance(item, tuple) and len(item) == 2:
                yield item[0], item[1]
            else:
                yield "content", item
        return

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if chat.summary:
        messages.append({
            "role": "system",
            "content": f"[خلاصه مکالمات قبلی برای حفظ context]\n{chat.summary}"
        })

    recent_messages = (
        Message.query
        .filter_by(chat_id=chat_id)
        .order_by(Message.created_at.desc())
        .limit(6)
        .all()
    )
    recent_messages.reverse()

    for msg in recent_messages:
        role = msg.role if msg.role in {"user", "assistant", "system"} else ("user" if getattr(msg, "is_user", False) else "assistant")
        content = (msg.content or "").strip()

        if not content:
            continue

        messages.append({
            "role": role,
            "content": content
        })

    cleaned_user_text = (user_text or "").strip()
    if not cleaned_user_text:
        yield "content", "❌ پیام کاربر خالی است."
        return

    messages.append({"role": "user", "content": cleaned_user_text})

    reply = qom_chat(messages)

    if not reply or not str(reply).strip():
        yield "content", "❌ پاسخی از مدل دریافت نشد."
        return

    for part in chunk_text(str(reply).strip(), chunk_size=220):
        if part:
            yield "content", part