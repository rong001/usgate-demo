#!/usr/bin/env python3
"""MOCK E2E suite for USGate Portal. MOCK_XUI=true, isolated temp SQLite."""
from __future__ import annotations

import asyncio
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

_TMP = tempfile.mkdtemp(prefix="usgate-e2e-")
_DB = Path(_TMP) / "e2e.db"
os.environ["MOCK_XUI"] = "true"
os.environ["MOCK_XUI_FALLBACK"] = "false"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_DB}"
os.environ["APP_SECRET_KEY"] = "e2e-test-secret-key-not-for-production-use-32b"
os.environ["BOOTSTRAP_ADMIN_USER"] = "admin"
os.environ["BOOTSTRAP_ADMIN_PASSWORD"] = "adminpass1"
os.environ["LOGIN_RATE_LIMIT"] = "5"
os.environ["LOGIN_RATE_WINDOW_SECONDS"] = "60"
os.environ["GLOBAL_RATE_LIMIT"] = "0"
os.environ["XUI_SUB_BASE_URL"] = "http://VPS_IP:2096/SUB_PATH"
os.environ["SESSION_HTTPS_ONLY"] = "false"

RESULTS: list[tuple[str, str, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, "PASS" if ok else "FAIL", detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def csrf_from(resp) -> str:
    tok = resp.cookies.get("usgate_csrf") or ""
    if tok:
        return tok
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', resp.text or "")
    return m.group(1) if m else ""


def find_user_disable_id(html: str, username: str) -> str | None:
    for m in re.finditer(r"<tr>(.*?)</tr>", html, re.S | re.I):
        row = m.group(1)
        if re.search(rf">\s*{re.escape(username)}\s*<", row) or f">{username}" in row:
            m2 = re.search(r"/admin/users/(\d+)/disable", row)
            if m2:
                return m2.group(1)
    return None


def main() -> int:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.config import clear_settings_cache, get_settings
    from app.rate_limit import reset_rate_buckets
    from app.xui_client import reset_mock_store, reset_xui_singleton

    clear_settings_cache()
    reset_xui_singleton()
    reset_mock_store()
    reset_rate_buckets()

    import app.database as database

    clear_settings_cache()
    settings = get_settings()
    assert settings.mock_xui is True

    database.engine = create_async_engine(
        settings.database_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    database.SessionLocal = async_sessionmaker(
        database.engine, expire_on_commit=False, class_=AsyncSession
    )

    import app.main as main_mod
    from fastapi.testclient import TestClient

    main_mod.app = main_mod.create_app()

    with TestClient(main_mod.app) as client:
        _suite(client, database, main_mod, AsyncSession, create_async_engine, async_sessionmaker)

    print("\n## MOCK E2E RESULTS\n")
    print("| # | Check | Result | Detail |")
    print("|---|-------|--------|--------|")
    for i, (name, status, detail) in enumerate(RESULTS, 1):
        print(f"| {i} | {name} | {status} | {detail.replace('|', '/')} |")
    failed = sum(1 for _, s, _ in RESULTS if s != "PASS")
    print(f"\nTotal: {len(RESULTS)}  PASS: {len(RESULTS)-failed}  FAIL: {failed}")
    return 0 if failed == 0 else 1


def _suite(client, database, main_mod, AsyncSession, create_async_engine, async_sessionmaker):
    from app.config import clear_settings_cache
    from app.rate_limit import reset_rate_buckets
    from app.xui_client import reset_xui_singleton
    from fastapi.testclient import TestClient

    # 1. Happy path
    r = client.get("/healthz")
    record(
        "healthz mock_xui true",
        r.status_code == 200 and r.json().get("mock_xui") is True,
        str(r.json()),
    )

    r = client.get("/login")
    csrf = csrf_from(r)
    record("login page + CSRF cookie", r.status_code == 200 and bool(csrf), f"csrf={bool(csrf)}")

    r = client.post(
        "/login",
        data={"username": "demo", "password": "demo1234", "csrf_token": csrf},
        follow_redirects=False,
    )
    record(
        "1. happy path login demo",
        r.status_code == 303 and r.headers.get("location") == "/dashboard",
        f"status={r.status_code} loc={r.headers.get('location')}",
    )

    r = client.get("/dashboard")
    body = r.text or ""
    has_traffic = ("Traffic used" in body or "已用" in body) and ("GB" in body or "MB" in body)
    has_expiry = "Expiry" in body or "到期" in body
    record(
        "1. dashboard traffic/expiry/masked sub",
        r.status_code == 200 and has_traffic and has_expiry and ("sub-masked" in body),
        f"traffic={has_traffic} expiry={has_expiry}",
    )
    client.get("/logout")

    # 2. Error paths
    reset_rate_buckets()
    r = client.get("/login")
    csrf = csrf_from(r)
    r = client.post(
        "/login",
        data={"username": "demo", "password": "WRONG", "csrf_token": csrf},
        follow_redirects=False,
    )
    record("2. bad password → 401", r.status_code == 401, f"status={r.status_code}")

    r = client.post(
        "/login",
        data={"username": "demo", "password": "demo1234", "csrf_token": "bogus"},
        follow_redirects=False,
    )
    record("2. missing/bad CSRF → 403", r.status_code == 403, f"status={r.status_code}")

    reset_rate_buckets()
    r = client.get("/login")
    csrf = csrf_from(r)
    hit_429 = False
    for _ in range(8):
        rr = client.post(
            "/login",
            data={"username": "nouser", "password": "x", "csrf_token": csrf},
            follow_redirects=False,
        )
        if rr.status_code == 401:
            csrf = csrf_from(rr) or csrf
        if rr.status_code == 429:
            hit_429 = True
            break
    record("2. rate-limit 429", hit_429, "login hammer")

    # 3. AuthZ
    reset_rate_buckets()
    r = client.get("/login")
    csrf = csrf_from(r)
    client.post(
        "/login",
        data={"username": "demo", "password": "demo1234", "csrf_token": csrf},
        follow_redirects=False,
    )
    r = client.get("/admin", follow_redirects=False)
    ok_admin = r.status_code == 303 and r.headers.get("location") == "/dashboard"
    record("3. user cannot hit admin", ok_admin, f"status={r.status_code}")

    r = client.get("/admin/audit", follow_redirects=False)
    ok_audit = r.status_code == 303
    record("3. user cannot hit admin audit", ok_audit, f"status={r.status_code}")

    client.get("/logout")
    reset_rate_buckets()
    r = client.get("/login")
    csrf = csrf_from(r)
    client.post(
        "/login",
        data={"username": "admin", "password": "adminpass1", "csrf_token": csrf},
        follow_redirects=False,
    )
    r = client.get("/admin")
    csrf = csrf_from(r)
    r = client.post(
        "/admin/users/create",
        data={
            "username": "alice",
            "password": "alicepass",
            "quota_gb": "10",
            "limit_ip": "1",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    record("3. admin create alice", r.status_code == 303, f"loc={r.headers.get('location')}")

    csrf = csrf_from(client.get("/admin"))
    r = client.post(
        "/admin/users/create",
        data={
            "username": "bob",
            "password": "bobpass1",
            "quota_gb": "10",
            "limit_ip": "1",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    record("3. admin create bob", r.status_code == 303, f"loc={r.headers.get('location')}")

    client.get("/logout")
    reset_rate_buckets()
    r = client.get("/login")
    csrf = csrf_from(r)
    client.post(
        "/login",
        data={"username": "alice", "password": "alicepass", "csrf_token": csrf},
        follow_redirects=False,
    )
    r = client.get("/dashboard")
    body = (r.text or "").lower()
    idor_ok = r.status_code == 200 and "bob" not in body
    record("3. user A cannot see user B data", idor_ok, "alice dashboard excludes bob")

    # 4. Disable + audit
    client.get("/logout")
    reset_rate_buckets()
    r = client.get("/login")
    csrf = csrf_from(r)
    client.post(
        "/login",
        data={"username": "admin", "password": "adminpass1", "csrf_token": csrf},
        follow_redirects=False,
    )
    r = client.get("/admin")
    csrf = csrf_from(r)
    alice_id = find_user_disable_id(r.text or "", "alice")
    disable_ok = False
    if alice_id:
        rr = client.post(
            f"/admin/users/{alice_id}/disable",
            data={"csrf_token": csrf},
            follow_redirects=False,
        )
        disable_ok = rr.status_code == 303
    record("4. admin disable user", disable_ok, f"alice_id={alice_id}")

    r = client.get("/admin/audit")
    audit_body = r.text or ""
    audit_ok = "disable_user" in audit_body and "alice" in audit_body
    no_secrets = "alicepass" not in audit_body and "http://VPS_IP:2096/SUB_PATH/" not in audit_body
    record("4. audit contains disable (no secrets)", audit_ok and no_secrets, f"secrets_clean={no_secrets}")

    client.get("/logout")
    reset_rate_buckets()
    r = client.get("/login")
    csrf = csrf_from(r)
    r = client.post(
        "/login",
        data={"username": "alice", "password": "alicepass", "csrf_token": csrf},
        follow_redirects=False,
    )
    record("4. disabled user login blocked", r.status_code == 401, f"status={r.status_code}")

    # 5. Restart persistence — new TestClient / engine, same DB file
    client.get("/logout")
    try:
        database.engine.sync_engine.dispose()
    except Exception:
        pass
    clear_settings_cache()
    reset_xui_singleton()
    database.engine = create_async_engine(
        f"sqlite+aiosqlite:///{_DB}",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    database.SessionLocal = async_sessionmaker(
        database.engine, expire_on_commit=False, class_=AsyncSession
    )
    main_mod.app = main_mod.create_app()
    with TestClient(main_mod.app) as client2:
        reset_rate_buckets()
        r = client2.get("/login")
        csrf = csrf_from(r)
        r = client2.post(
            "/login",
            data={"username": "demo", "password": "demo1234", "csrf_token": csrf},
            follow_redirects=False,
        )
        demo_ok = r.status_code == 303
        client2.get("/logout")
        r = client2.get("/login")
        csrf = csrf_from(r)
        client2.post(
            "/login",
            data={"username": "admin", "password": "adminpass1", "csrf_token": csrf},
            follow_redirects=False,
        )
        r = client2.get("/admin/audit")
        persist_audit = any(
            x in (r.text or "") for x in ("disable_user", "create_user", "bootstrap_admin")
        )
        record(
            "5. sqlite survives restart (users+audit)",
            demo_ok and persist_audit,
            f"demo_login={demo_ok} audit={persist_audit}",
        )

        # 6. Demo reset
        r = client2.get("/admin")
        csrf = csrf_from(r)
        r = client2.post(
            "/admin/demo-reset",
            data={"csrf_token": csrf},
            follow_redirects=False,
        )
        loc = r.headers.get("location") or ""
        record("6. admin demo-reset", r.status_code == 303 and "demo_reset_ok" in loc, f"loc={loc}")

        client2.get("/logout")
        reset_rate_buckets()
        r = client2.get("/login")
        csrf = csrf_from(r)
        r = client2.post(
            "/login",
            data={"username": "alice", "password": "alicepass", "csrf_token": csrf},
            follow_redirects=False,
        )
        record("6. after reset alice gone", r.status_code == 401, f"status={r.status_code}")

        r = client2.get("/login")
        csrf = csrf_from(r)
        r = client2.post(
            "/login",
            data={"username": "demo", "password": "demo1234", "csrf_token": csrf},
            follow_redirects=False,
        )
        record("6. after reset demo works", r.status_code == 303, f"status={r.status_code}")


if __name__ == "__main__":
    raise SystemExit(main())
