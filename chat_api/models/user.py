from ..extensions import db

class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    chats = db.relationship("Chat", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {"user_id": self.user_id, "username": self.username}