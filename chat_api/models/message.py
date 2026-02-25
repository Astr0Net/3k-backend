from datetime import datetime
from ..extensions import db

class Message(db.Model):
    __tablename__ = "messages"

    message_id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey("chats.chat_id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    time = db.Column(db.String(255))
    is_user = db.Column(db.Boolean, nullable=False)

    chat = db.relationship("Chat", back_populates="messages")

    def to_dict(self):
        return {
            "message_id": self.message_id,
            "chat_id": self.chat_id,
            "content": self.content,
            "time": self.time,
            "is_user": self.is_user,
        }

    @staticmethod
    def now_as_string():
        return datetime.utcnow().isoformat()