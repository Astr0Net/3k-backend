from datetime import datetime, timezone
from ..extensions import db


class Message(db.Model):
    __tablename__ = "messages"

    message_id = db.Column(db.BigInteger, primary_key=True)

    chat_id = db.Column(
        db.Integer,
        db.ForeignKey("chats.chat_id"),
        nullable=False,
        index=True
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False,
        index=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    chat = db.relationship(
        "Chat",
        back_populates="messages"
    )

    def to_dict(self):
        return {
            "message_id": self.message_id,
            "chat_id": self.chat_id,
            "content": self.content,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
