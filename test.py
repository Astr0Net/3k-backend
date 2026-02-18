from app import create_app
from chat_api.extensions import db

app = create_app()

with app.app_context():
    db.create_all()
    print("✅ tables created")
