from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError

from ..extensions import db, bcrypt
from chat_api.models.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(username=username, password=hashed_pw)

    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "username already exists"}), 409

    return jsonify({"message": "user created", "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "invalid username or password"}), 401

    # فعلاً ساده: فقط اطلاعات کاربر را برمی‌گردانیم
    # در نسخه حرفه‌ای‌تر می‌تونی اینجا JWT برگردونی
    return jsonify({"message": "login successful", "user": user.to_dict()}), 200
