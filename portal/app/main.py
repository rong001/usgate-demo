"""USGate Portal — FastAPI entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select

from app.auth import hash_password
from app.config import get_settings
from app.database import SessionLocal, init_db
from app.models import AuditLog, User
from app.routers import admin, auth_routes, user
from app.xui_client import get_xui

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
# Ensure subscription URLs never appear: filter any logger message containing '2096/' or 'subId='
class _RedactFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if "subscription" in msg.lower() and ("http://" in msg or "https://" in msg):
            record.msg = "[redacted subscription URL log line]"
            record.args = ()
        return True


logging.getLogger().addFilter(_RedactFilter())


async def bootstrap_admin() -> None:
    settings = get_settings()
    async with SessionLocal() as db:
        count = await db.scalar(select(func.count()).select_from(User))
        if count and count > 0:
            return
        admin_user = User(
            username=settings.bootstrap_admin_user,
            password_hash=hash_password(settings.bootstrap_admin_password),
            is_admin=True,
            is_active=True,
            notes="bootstrap admin",
        )
        db.add(admin_user)
        db.add(
            AuditLog(
                actor_username="system",
                action="bootstrap_admin",
                target=settings.bootstrap_admin_user,
                detail="initial admin created",
            )
        )
        # Optionally map demo portal users to mock XUI clients
        xui = get_xui()
        demo = await xui.get_client("demo-user1")
        if demo:
            demo_user = User(
                username="demo",
                password_hash=hash_password("demo1234"),
                is_admin=False,
                is_active=True,
                xui_email=demo.email,
                xui_uuid=demo.uuid,
                xui_sub_id=demo.sub_id,
                quota_bytes=demo.total_bytes,
                limit_ip=demo.limit_ip,
                notes="seeded demo user (mock)",
            )
            db.add(demo_user)
        await db.commit()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Path("data").mkdir(parents=True, exist_ok=True)
    await init_db()
    await bootstrap_admin()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan, docs_url=None, redoc_url=None)

    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    app.include_router(auth_routes.router)
    app.include_router(user.router)
    app.include_router(admin.router)

    @app.get("/healthz")
    async def healthz():
        return {
            "ok": True,
            "mock_xui": get_xui().is_mock,
            "app": settings.app_name,
        }

    @app.exception_handler(303)
    async def see_other(_request: Request, exc):  # pragma: no cover
        return JSONResponse({"detail": "redirect"}, status_code=303)

    return app


app = create_app()
