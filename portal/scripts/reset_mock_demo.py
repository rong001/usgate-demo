#!/usr/bin/env python3
"""CLI: reseed MOCK demo users/audit without touching a real 3X-UI panel.

Usage (from portal root, MOCK_XUI=true):
  python scripts/reset_mock_demo.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

# Force mock unless already set
os.environ.setdefault("MOCK_XUI", "true")


async def main() -> int:
    from sqlalchemy import select

    from app.auth import hash_password
    from app.config import clear_settings_cache, get_settings
    from app.database import SessionLocal, init_db
    from app.models import AuditLog, User
    from app.rate_limit import reset_rate_buckets
    from app.xui_client import get_xui, reset_mock_store, reset_xui_singleton

    clear_settings_cache()
    reset_xui_singleton()
    settings = get_settings()
    if not settings.mock_xui:
        print("REFUSE: MOCK_XUI is false — will not reset against live panel")
        return 2

    Path("data").mkdir(parents=True, exist_ok=True)
    await init_db()
    reset_mock_store()
    reset_rate_buckets()
    xui = get_xui()

    async with SessionLocal() as db:
        for u in (await db.execute(select(User))).scalars().all():
            await db.delete(u)
        for row in (await db.execute(select(AuditLog))).scalars().all():
            await db.delete(row)
        await db.flush()

        db.add(
            User(
                username=settings.bootstrap_admin_user,
                password_hash=hash_password(settings.bootstrap_admin_password),
                is_admin=True,
                is_active=True,
                notes="bootstrap admin (cli reset)",
            )
        )
        demo = await xui.get_client("demo-user1")
        if demo:
            db.add(
                User(
                    username="demo",
                    password_hash=hash_password("demo1234"),
                    is_admin=False,
                    is_active=True,
                    xui_email=demo.email,
                    xui_uuid=demo.uuid,
                    xui_sub_id=demo.sub_id,
                    quota_bytes=demo.total_bytes,
                    limit_ip=demo.limit_ip,
                    notes="seeded demo user (cli reset)",
                )
            )
        db.add(
            AuditLog(
                actor_username="system",
                action="demo_reset",
                target="mock",
                detail="cli reseed; no real panel touched",
            )
        )
        await db.commit()

    print("OK: mock demo reseeded (admin + demo). No real panel touched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
