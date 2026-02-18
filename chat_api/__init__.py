import os
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from .extensions import db, bcrypt, jwt
from .models.models import TokenBlocklist


def _get_allowed_origins():
    """
    خواندن لیست originهای مجاز از ENV.
    نمونه:
      CORS_ORIGINS=http://localhost:5173,https://your-frontend.com
    """
    raw = os.getenv("CORS_ORIGINS", "").strip()

    # اگر تنظیم نکردی، برای dev راحت باشه
    if not raw:
        return ["http://localhost:5173"]

    return [o.strip() for o in raw.split(",") if o.strip()]


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    allowed_origins = _get_allowed_origins()

    # ✅ CORS مناسب برای React + JWT در Authorization header
    CORS(
        app,
        resources={r"/api/*": {"origins": allowed_origins}},
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Content-Type"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        max_age=86400,  # cache preflight for 24h
        supports_credentials=False,  # چون JWT در header می‌فرستی
    )

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # اگر توکن revoke شده بود، از اینجا بلاک میشه
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload.get("jti")
        if not jti:
            return True
        return db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar() is not None

    # خطاهای JWT به صورت JSON تمیز
    @jwt.unauthorized_loader
    def jwt_missing_token(reason):
        return jsonify({"error": f"missing token: {reason}"}), 401

    @jwt.invalid_token_loader
    def jwt_invalid_token(reason):
        return jsonify({"error": f"invalid token: {reason}"}), 401

    @jwt.expired_token_loader
    def jwt_expired_token(jwt_header, jwt_payload):
        return jsonify({"error": "token expired"}), 401

    @jwt.revoked_token_loader
    def jwt_revoked_token(jwt_header, jwt_payload):
        return jsonify({"error": "token revoked"}), 401

    # ثبت بلوپرینت‌ها
    from .routes.auth import auth_bp
    from .routes.chat import chat_bp
    from .routes.message import message_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(message_bp, url_prefix="/api")

    # ساخت جداول
    with app.app_context():
        db.create_all()

    return app
