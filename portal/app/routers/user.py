"""End-user portal: subscription, traffic, devices, reset sub token."""
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.csrf import get_csrf_token, new_csrf_token, set_csrf_cookie, validate_csrf
from app.database import get_db
from app.deps import current_user, redirect_login
from app.models import AuditLog, User
from app.rate_limit import client_ip
from app.util import format_bytes, format_expiry
from app.xui_client import get_xui, mask_url

router = APIRouter(tags=["user"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def root(user: Annotated[User | None, Depends(current_user)]):
    if not user:
        return RedirectResponse("/login", status_code=303)
    return RedirectResponse("/admin" if user.is_admin else "/dashboard", status_code=303)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: Annotated[User | None, Depends(current_user)],
):
    if not user:
        return redirect_login()
    if user.is_admin and not user.xui_email:
        return RedirectResponse("/admin", status_code=303)

    xui = get_xui()
    info = None
    sub_url = ""
    masked = ""
    ips: list[str] = []
    if user.xui_email:
        info = await xui.get_client(user.xui_email)
        if info:
            sub_url = info.subscription_url(get_settings().xui_sub_base_url)
            masked = mask_url(sub_url)
            ips = await xui.get_client_ips(user.xui_email)

    ctx = {
        "request": request,
        "user": user,
        "info": info,
        "sub_url": sub_url,
        "sub_masked": masked,
        "ips": ips,
        "format_bytes": format_bytes,
        "format_expiry": format_expiry,
        "csrf_token": get_csrf_token(request),
        "app_name": get_settings().app_name,
        "mock_mode": xui.is_mock,
        "flash": request.query_params.get("flash"),
    }
    tok = get_csrf_token(request) or new_csrf_token()
    ctx["csrf_token"] = tok
    resp = templates.TemplateResponse("user_dashboard.html", ctx)
    set_csrf_cookie(resp, tok)
    return resp


@router.post("/dashboard/reset-sub")
async def reset_sub(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(current_user)],
    csrf_token: Annotated[str, Form()] = "",
):
    if not user:
        return redirect_login()
    validate_csrf(request, csrf_token)
    if not user.xui_email:
        return RedirectResponse("/dashboard?flash=no_client", status_code=303)

    xui = get_xui()
    new_sub = await xui.reset_sub_id(user.xui_email)
    if new_sub:
        user.xui_sub_id = new_sub
        db.add(
            AuditLog(
                actor_username=user.username,
                action="reset_sub_token",
                target=user.xui_email,
                detail="user self-service (sub id rotated; URL not logged)",
                ip=client_ip(request),
            )
        )
        await db.commit()
    return RedirectResponse("/dashboard?flash=sub_reset", status_code=303)


@router.post("/dashboard/clear-ips")
async def clear_ips(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(current_user)],
    csrf_token: Annotated[str, Form()] = "",
):
    """Best-effort clear of stored IPs if panel API supports it; mock clears local list."""
    if not user:
        return redirect_login()
    validate_csrf(request, csrf_token)
    if not user.xui_email:
        return RedirectResponse("/dashboard", status_code=303)

    xui = get_xui()
    await xui.clear_client_ips(user.xui_email)
    db.add(
        AuditLog(
            actor_username=user.username,
            action="clear_ips",
            target=user.xui_email,
            detail="self-service clear device/IP list",
            ip=client_ip(request),
        )
    )
    await db.commit()
    return RedirectResponse("/dashboard?flash=ips_cleared", status_code=303)
