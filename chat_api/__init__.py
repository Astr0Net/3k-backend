from flask import Flask
from flask_cors import CORS
from config import Config
from .extensions import db, bcrypt


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # CORS برای اتصال ری‌اکت (مثال: localhost:5173 برای Vite)
    CORS(app)

    db.init_app(app)
    bcrypt.init_app(app)

    # ثبت بلوپرینت‌ها
    from .routes.auth import auth_bp
    from .routes.chat import chat_bp
    from .routes.message import message_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(message_bp, url_prefix="/api")

    # ساخت جداول اگر نبود
    with app.app_context():
        db.create_all()

    return app
