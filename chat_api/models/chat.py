from ..extensions import db

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
        data = {"chat_id": self.chat_id, "user_id": self.user_id, "title": self.title}
        if include_messages:
            data["messages"] = [m.to_dict() for m in self.messages]
        return data