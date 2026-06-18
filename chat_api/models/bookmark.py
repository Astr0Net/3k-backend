from datetime import datetime, timezone
from ..extensions import db


class Bookmark(db.Model):
    __tablename__ = "bookmarks"

    id = db.Column(db.BigInteger, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # اطلاعات شغل — مستقیم از کارت SSE ذخیره می‌شود
    job_url = db.Column(db.Text, nullable=False)
    job_title = db.Column(db.Text, nullable=True)
    company_name = db.Column(db.Text, nullable=True)
    location = db.Column(db.Text, nullable=True)
    paycheck = db.Column(db.Text, nullable=True)
    source_site = db.Column(db.Text, nullable=True)
    match_percent = db.Column(db.Integer, nullable=True)
    requirements = db.Column(db.JSON, nullable=True)
    company_reviews = db.Column(db.JSON, nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    user = db.relationship("User", backref="bookmarks")

    # هر کاربر یک job_url را فقط یکبار بوک‌مارک کند
    __table_args__ = (
        db.UniqueConstraint("user_id", "job_url", name="uq_bookmark_user_job"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "job_url": self.job_url,
            "job_title": self.job_title,
            "company_name": self.company_name,
            "location": self.location,
            "paycheck": self.paycheck,
            "source_site": self.source_site,
            "match_percent": self.match_percent,
            "requirements": self.requirements,
            "company_reviews": self.company_reviews,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }