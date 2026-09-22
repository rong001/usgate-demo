"""Simple double-submit CSRF token (cookie + form field)."""
import secrets
from typing import Annotated

from fastapi import Form, HTTPException, Request, Response

from app.config import get_settings

CSRF_COOKIE = "usgate_csrf"


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def set_csrf_cookie(response: Response, token: str) -> None:
    s = get_settings()
    response.set_cookie(
        key=CSRF_COOKIE,
        value=token,
        httponly=False,
        samesite="lax",
        secure=s.session_https_only,
        max_age=s.session_max_age_seconds,
        path="/",
    )


def ensure_csrf_cookie(response: Response, request: Request) -> str:
    """Reuse existing cookie token or mint one; always set on response."""
    token = request.cookies.get(CSRF_COOKIE) or new_csrf_token()
    set_csrf_cookie(response, token)
    return token


def get_csrf_token(request: Request) -> str:
    return request.cookies.get(CSRF_COOKIE) or ""


def validate_csrf(request: Request, form_token: str) -> None:
    cookie_token = request.cookies.get(CSRF_COOKIE)
    if not cookie_token or not form_token or not secrets.compare_digest(cookie_token, form_token):
        raise HTTPException(status_code=403, detail="CSRF validation failed")


async def require_csrf(
    request: Request,
    csrf_token: Annotated[str, Form()] = "",
) -> None:
    validate_csrf(request, csrf_token)
