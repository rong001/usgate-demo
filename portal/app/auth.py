"""Password hashing + session cookie helpers."""
from typing import Any

import bcrypt
from fastapi import Request, Response
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import get_settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def _serializer() -> URLSafeTimedSerializer:
    s = get_settings()
    return URLSafeTimedSerializer(s.app_secret_key, salt="usgate-session")


def create_session_token(data: dict[str, Any]) -> str:
    return _serializer().dumps(data)


def load_session_token(token: str) -> dict[str, Any] | None:
    s = get_settings()
    try:
        return _serializer().loads(token, max_age=s.session_max_age_seconds)
    except (BadSignature, SignatureExpired):
        return None


def set_session_cookie(response: Response, data: dict[str, Any]) -> None:
    s = get_settings()
    token = create_session_token(data)
    response.set_cookie(
        key=s.session_cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        secure=s.session_https_only,
        max_age=s.session_max_age_seconds,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    s = get_settings()
    response.delete_cookie(s.session_cookie_name, path="/")


def get_session(request: Request) -> dict[str, Any] | None:
    s = get_settings()
    token = request.cookies.get(s.session_cookie_name)
    if not token:
        return None
    return load_session_token(token)
