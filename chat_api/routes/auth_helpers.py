from flask import jsonify


def api_ok(data=None, message="ok", http_status=200):
    payload = {"status": http_status, "message": message, "data": data}
    return jsonify(payload), http_status


def api_error(message="error", http_status=400, data=None):
    payload = {"status": http_status, "error": message, "data": data}
    return jsonify(payload), http_status


def normalize_username(u: str) -> str:
    return (u or "").strip().lower()