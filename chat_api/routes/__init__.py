from flask import Blueprint
from dotenv import load_dotenv
load_dotenv()

# ساخت Blueprint اصلی که همه‌ی مسیرها زیر آن قرار می‌گیرند
api = Blueprint('api', __name__)

# ایمپورت کردن فایل‌های مربوط به مسیرها (auth.py و chat.py)
from . import auth, chat, message, landing
