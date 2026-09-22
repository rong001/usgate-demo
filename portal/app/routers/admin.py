"""Admin: create/disable users, quotas, audit log."""
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import hash_password
from app.config import get_settings
from app.csrf import get_csrf_token, new_csrf_token, set_csrf_cookie, validate_csrf
from app.database import get_db
from app.deps import current_user, redirect_login
from app.models import AuditLog, User
from app.rate_limit import client_ip
from app.util import format_bytes
from app.xui_client import XUIError, get_xui

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")


def _require_admin(user: User | None):
    if not user:
        return redirect_login()
    if not user.is_admin:
        return RedirectResponse("/dashboard", status_code=303)
    return None


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def admin_home(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(current_user)],
):
    denied = _require_admin(user)
    if denied:
        return denied

    result = await db.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    xui = get_xui()
    # enrich with live/mock traffic
    traffic: dict[str, dict] = {}
    for u in users:
        if u.xui_email:
            info = await xui.get_client(u.xui_email)
            if info:
                traffic[u.xui_email] = {
                    "used": format_bytes(info.used_bytes),
                    "total": format_bytes(info.total_bytes) if info.total_bytes else "∞",
                    "online": info.online,
                    "enable": info.enable,
                }

    ctx = {
        "request": request,
        "user": user,
        "users": users,
        "traffic": traffic,
        "csrf_token": get_csrf_token(request),
        "app_name": get_settings().app_name,
        "mock_mode": xui.is_mock,
        "flash": request.query_params.get("flash"),
        "format_bytes": format_bytes,
    }
    tok = get_csrf_token(request) or new_csrf_token()
    ctx["csrf_token"] = tok
    resp = templates.TemplateResponse("admin_dashboard.html", ctx)
    set_csrf_cookie(resp, tok)
    return resp


@router.post("/users/create")
async def create_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User | None, Depends(current_user)],
    username: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
    quota_gb: Annotated[int, Form()] = 50,
    limit_ip: Annotated[int, Form()] = 2,
    csrf_token: Annotated[str, Form()] = "",
):
    denied = _require_admin(admin)
    if denied:
        return denied
    validate_csrf(request, csrf_token)

    username = username.strip().lower()
    if not username or not password or len(password) < 6:
        return RedirectResponse("/admin?flash=invalid_input", status_code=303)

    existing = await db.execute(select(User).where(User.username == username))
    if existing.scalar_one_or_none():
        return RedirectResponse("/admin?flash=user_exists", status_code=303)

    xui_email = username  # map 1:1
    xui = get_xui()
    try:
        info = await xui.create_client(email=xui_email, total_gb=quota_gb, limit_ip=limit_ip)
    except XUIError as e:
        db.add(
            AuditLog(
                actor_username=admin.username,
                action="create_user_failed",
                target=username,
                detail=f"code={e.code}",
                ip=client_ip(request),
            )
        )
        await db.commit()
        return RedirectResponse(f"/admin?flash=xui_error_{e.code}", status_code=303)

    user = User(
        username=username,
        password_hash=hash_password(password),
        is_admin=False,
        is_active=True,
        xui_email=xui_email,
        xui_uuid=info.uuid,
        xui_sub_id=info.sub_id,
        quota_bytes=quota_gb * (1024**3),
        limit_ip=limit_ip,
    )
    db.add(user)
    db.add(
        AuditLog(
            actor_username=admin.username,
            action="create_user",
            target=username,
            detail=f"quota_gb={quota_gb} limit_ip={limit_ip} mock={xui.is_mock}",
            ip=client_ip(request),
        )
    )
    await db.commit()
    return RedirectResponse("/admin?flash=created", status_code=303)


@router.post("/users/{user_id}/disable")
async def disable_user(
    user_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User | None, Depends(current_user)],
    csrf_token: Annotated[str, Form()] = "",
):
    denied = _require_admin(admin)
    if denied:
        return denied
    validate_csrf(request, csrf_token)

    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target or target.is_admin:
        return RedirectResponse("/admin?flash=not_found", status_code=303)

    target.is_active = False
    xui = get_xui()
    if target.xui_email:
        await xui.set_enable(target.xui_email, False)
    db.add(
        AuditLog(
            actor_username=admin.username,
            action="disable_user",
            target=target.username,
            detail="portal+panel disable",
            ip=client_ip(request),
        )
    )
    await db.commit()
    return RedirectResponse("/admin?flash=disabled", status_code=303)


@router.post("/users/{user_id}/enable")
async def enable_user(
    user_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User | None, Depends(current_user)],
    csrf_token: Annotated[str, Form()] = "",
):
    denied = _require_admin(admin)
    if denied:
        return denied
    validate_csrf(request, csrf_token)

    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        return RedirectResponse("/admin?flash=not_found", status_code=303)

    target.is_active = True
    xui = get_xui()
    if target.xui_email:
        await xui.set_enable(target.xui_email, True)
    db.add(
        AuditLog(
            actor_username=admin.username,
            action="enable_user",
            target=target.username,
            detail="portal+panel enable",
            ip=client_ip(request),
        )
    )
    await db.commit()
    return RedirectResponse("/admin?flash=enabled", status_code=303)


@router.post("/users/{user_id}/quota")
async def set_quota(
    user_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User | None, Depends(current_user)],
    quota_gb: Annotated[int, Form()] = 50,
    limit_ip: Annotated[int, Form()] = 2,
    csrf_token: Annotated[str, Form()] = "",
):
    denied = _require_admin(admin)
    if denied:
        return denied
    validate_csrf(request, csrf_token)

    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        return RedirectResponse("/admin?flash=not_found", status_code=303)

    target.quota_bytes = max(0, quota_gb) * (1024**3)
    target.limit_ip = max(0, limit_ip)
    xui = get_xui()
    if target.xui_email:
        await xui.update_quota(target.xui_email, quota_gb, limit_ip)
    db.add(
        AuditLog(
            actor_username=admin.username,
            action="set_quota",
            target=target.username,
            detail=f"quota_gb={quota_gb} limit_ip={limit_ip}",
            ip=client_ip(request),
        )
    )
    await db.commit()
    return RedirectResponse("/admin?flash=quota_updated", status_code=303)


@router.get("/audit", response_class=HTMLResponse)
async def audit_log(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(current_user)],
):
    denied = _require_admin(user)
    if denied:
        return denied

    result = await db.execute(
        select(AuditLog).order_by(AuditLog.id.desc()).limit(200)
    )
    logs = result.scalars().all()
    ctx = {
        "request": request,
        "user": user,
        "logs": logs,
        "csrf_token": get_csrf_token(request),
        "app_name": get_settings().app_name,
        "mock_mode": get_xui().is_mock,
    }
    tok = get_csrf_token(request) or new_csrf_token()
    ctx["csrf_token"] = tok
    resp = templates.TemplateResponse("admin_audit.html", ctx)
    set_csrf_cookie(resp, tok)
    return resp


@router.post("/demo-reset")
async def demo_reset(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User | None, Depends(current_user)],
    csrf_token: Annotated[str, Form()] = "",
):
    """
    Admin-only MOCK demo reseed.
    Wipes portal users/audit (except recreating bootstrap admin + demo),
    resets in-memory mock panel clients. Refuses when MOCK_XUI=false.
    """
    denied = _require_admin(admin)
    if denied:
        return denied
    validate_csrf(request, csrf_token)

    settings = get_settings()
    xui = get_xui()
    if not settings.mock_xui or not xui.is_mock:
        return RedirectResponse("/admin?flash=demo_reset_blocked_live", status_code=303)

    from app.auth import hash_password
    from app.rate_limit import reset_rate_buckets
    from app.xui_client import reset_mock_store

    # Delete all users + audit
    existing = await db.execute(select(User))
    for u in existing.scalars().all():
        await db.delete(u)
    logs = await db.execute(select(AuditLog))
    for row in logs.scalars().all():
        await db.delete(row)
    await db.flush()

    reset_mock_store()
    reset_rate_buckets()

    admin_user = User(
        username=settings.bootstrap_admin_user,
        password_hash=hash_password(settings.bootstrap_admin_password),
        is_admin=True,
        is_active=True,
        notes="bootstrap admin (demo-reset)",
    )
    db.add(admin_user)

    demo_info = await xui.get_client("demo-user1")
    if demo_info:
        db.add(
            User(
                username="demo",
                password_hash=hash_password("demo1234"),
                is_admin=False,
                is_active=True,
                xui_email=demo_info.email,
                xui_uuid=demo_info.uuid,
                xui_sub_id=demo_info.sub_id,
                quota_bytes=demo_info.total_bytes,
                limit_ip=demo_info.limit_ip,
                notes="seeded demo user (mock reset)",
            )
        )

    db.add(
        AuditLog(
            actor_username=admin.username if admin else "admin",
            action="demo_reset",
            target="mock",
            detail="reseeded synthetic users; no real panel touched",
            ip=client_ip(request),
        )
    )
    await db.commit()
    return RedirectResponse("/admin?flash=demo_reset_ok", status_code=303)
