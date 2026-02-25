from datetime import datetime
from ..extensions import db

class Company(db.Model):
    __tablename__ = "companies"

    company_id = db.Column(db.BigInteger, primary_key=True)
    company_name = db.Column(db.Text, unique=True, nullable=False)

    reviews = db.Column(db.JSON, nullable=True)

    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)