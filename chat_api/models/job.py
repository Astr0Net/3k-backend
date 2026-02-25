from pgvector.sqlalchemy import Vector
from ..extensions import db

class Job(db.Model):
    __tablename__ = "jobs"

    job_id = db.Column(db.BigInteger, primary_key=True)
    job_url = db.Column(db.Text, unique=True, nullable=False)

    source_site = db.Column(db.Text, nullable=True)
    job_title = db.Column(db.Text, nullable=True)
    company_name = db.Column(db.Text, nullable=True)

    location = db.Column(db.Text, nullable=True)
    paycheck = db.Column(db.Text, nullable=True)
    requirements = db.Column(db.JSON, nullable=True)

    raw_text = db.Column(db.Text, nullable=False)

    embedding = db.Column(Vector(1536), nullable=True)