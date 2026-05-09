from datetime import datetime, timezone
from chat_api.extensions import db


class Resume(db.Model):
    __tablename__ = "resumes"  # بهتره plural باشه

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = db.relationship("Users", backref="resumes")

    def __repr__(self):
        return f"<Resume {self.id} - {self.title}>"
