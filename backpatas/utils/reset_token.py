# backpatas/utils/reset_token.py
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app

def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

def generate_reset_token(user_id: int, password_hash: str) -> str:
    s = _serializer()
    return s.dumps({"uid": user_id, "pwh": password_hash}, salt="pwd-reset")

def verify_reset_token(token: str, max_age_seconds: int):
    s = _serializer()
    try:
        return s.loads(token, salt="pwd-reset", max_age=max_age_seconds)
    except SignatureExpired:
        return "expired"
    except BadSignature:
        return None
