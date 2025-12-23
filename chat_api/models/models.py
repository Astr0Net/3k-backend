from datetime import datetime
from ..extensions import db


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    chats = db.relationship("Chat", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
        }

class Chat(db.Model):
    __tablename__ = "chats"

    chat_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    title = db.Column(db.String(255))

    summary = db.Column(db.Text, nullable=True)

    last_summarized_message_id = db.Column(db.Integer, nullable=True)

    user = db.relationship("User", back_populates="chats")
    messages = db.relationship("Message", back_populates="chat", cascade="all, delete-orphan")

    def to_dict(self, include_messages=False):
        data = {
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "title": self.title,
        }
        if include_messages:
            data["messages"] = [m.to_dict() for m in self.messages]
        return data


class Message(db.Model):
    __tablename__ = "messages"

    message_id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey("chats.chat_id"), nullable=False)
    content = db.Column(db.String(255), nullable=False)
    time = db.Column(db.String(255))  # طبق دیتابیس تو، ولی بهتره در عمل datetime باشه
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
