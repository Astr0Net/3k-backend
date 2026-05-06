from datetime import datetime
from ..extensions import db

class TokenBlocklist(db.Model):
    __tablename__ = "token_blocklist"

    id = db.Column(db.BigInteger, primary_key=True)
    jti = db.Column(db.String(36), unique=True, nullable=False, index=True)
    token_type = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    revoked_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)