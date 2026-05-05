from datetime import datetime, timezone
from ..extensions import db


class Chat(db.Model):
    __tablename__ = "chats"

    chat_id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False,
        index=True
    )

    title = db.Column(
        db.String(255),
        nullable=False,
        default="گفتگوی جدید"
    )

    summary = db.Column(
        db.Text,
        nullable=True
    )

    last_summarized_message_id = db.Column(
        db.Integer,
        nullable=True,
        index=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    user = db.relationship(
        "User",
        back_populates="chats"
    )

    messages = db.relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )

    def to_dict(self, include_messages=False):
        data = {
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "title": self.title,
            "summary": self.summary,
            "last_summarized_message_id": self.last_summarized_message_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "has_summary": bool(self.summary)
        }

        if include_messages:
            data["messages"] = [message.to_dict() for message in self.messages]

        return data
