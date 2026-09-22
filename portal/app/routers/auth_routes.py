"""Login / logout."""
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import clear_session_cookie, set_session_cookie, verify_password
from app.config import get_settings
from app.csrf import ensure_csrf_cookie, get_csrf_token, new_csrf_token, set_csrf_cookie, validate_csrf
from app.database import get_db
from app.deps import current_user
from app.models import AuditLog, User
from app.rate_limit import check_login_rate, client_ip

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


def _login_response(request: Request, error: str | None = None, status: int = 200):
    tok = get_csrf_token(request) or new_csrf_token()
    settings = get_settings()
    resp = templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": error,
            "csrf_token": tok,
            "app_name": settings.app_name,
            "mock_mode": settings.mock_xui,
        },
        status_code=status,
    )
    set_csrf_cookie(resp, tok)
    return resp


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    user: Annotated[User | None, Depends(current_user)],
):
    if user:
        dest = "/admin" if user.is_admin else "/dashboard"
        return RedirectResponse(dest, status_code=303)
    return _login_response(request)


@router.post("/login")
async def login_post(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    username: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
    csrf_token: Annotated[str, Form()] = "",
):
    check_login_rate(request)
    validate_csrf(request, csrf_token)

    result = await db.execute(select(User).where(User.username == username.strip()))
    user = result.scalar_one_or_none()
    ok = user and user.is_active and verify_password(password, user.password_hash)

    if not ok:
        return _login_response(
            request,
            error="Invalid username or password / 用户名或密码错误",
            status=401,
        )

    dest = "/admin" if user.is_admin else "/dashboard"
    response = RedirectResponse(dest, status_code=303)
    set_session_cookie(
        response,
        {"uid": user.id, "username": user.username, "is_admin": user.is_admin},
    )
    ensure_csrf_cookie(response, request)
    db.add(
        AuditLog(
            actor_username=user.username,
            action="login",
            target=user.username,
            detail="success",
            ip=client_ip(request),
        )
    )
    await db.commit()
    return response


@router.post("/logout")
async def logout(
    request: Request,
    csrf_token: Annotated[str, Form()] = "",
):
    validate_csrf(request, csrf_token)
    response = RedirectResponse("/login", status_code=303)
    clear_session_cookie(response)
    return response


@router.get("/logout")
async def logout_get():
    response = RedirectResponse("/login", status_code=303)
    clear_session_cookie(response)
    return response
