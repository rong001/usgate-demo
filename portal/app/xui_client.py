"""
3X-UI panel API client with mock mode.

Real endpoints follow 3X-UI v2/v3 style (panel/api/...).
Subscription URLs are NEVER written to logs.
"""
from __future__ import annotations

import logging
import secrets
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.config import get_settings

log = logging.getLogger("usgate.xui")


@dataclass
class ClientInfo:
    email: str
    uuid: str
    sub_id: str
    enable: bool = True
    total_bytes: int = 0
    up: int = 0
    down: int = 0
    expiry_ms: int = 0
    limit_ip: int = 2
    online: bool = False
    last_online: int | None = None
    ips: list[str] = field(default_factory=list)

    @property
    def used_bytes(self) -> int:
        return int(self.up) + int(self.down)

    @property
    def remaining_bytes(self) -> int:
        if self.total_bytes <= 0:
            return -1  # unlimited
        return max(0, self.total_bytes - self.used_bytes)

    def subscription_url(self, sub_base: str) -> str:
        base = sub_base.rstrip("/")
        return f"{base}/{self.sub_id}"


def mask_url(url: str, keep: int = 8) -> str:
    """Mask middle of URL for display; never log the full URL."""
    if len(url) <= keep * 2 + 3:
        return url[:4] + "…" + url[-4:] if len(url) > 8 else "****"
    return url[:keep] + "…" + url[-keep:]


# ---------- Mock store ----------
class _MockStore:
    def __init__(self) -> None:
        self.clients: dict[str, ClientInfo] = {}
        # seed demo clients matching docs placeholders
        self._seed()

    def _seed(self) -> None:
        demo = [
            ("demo-admin", 200 * 1024**3, 3, True),
            ("demo-user1", 50 * 1024**3, 2, False),
        ]
        for email, total, lim, online in demo:
            uid = str(uuid.uuid4())
            sub = str(uuid.uuid4())
            self.clients[email] = ClientInfo(
                email=email,
                uuid=uid,
                sub_id=sub,
                enable=True,
                total_bytes=total,
                up=1024**3 if email == "demo-user1" else 0,
                down=5 * 1024**3 if email == "demo-user1" else 2 * 1024**3,
                expiry_ms=0,
                limit_ip=lim,
                online=online,
                last_online=None,
                ips=["203.0.113.10", "198.51.100.22"][:lim] if online else [],
            )


_mock = _MockStore()


class XUIClient:
    """Talks to 3X-UI or serves mock data when MOCK_XUI=true / panel unreachable."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._cookie: str | None = None
        self._use_mock = self.settings.mock_xui

    @property
    def is_mock(self) -> bool:
        return self._use_mock

    def _headers(self) -> dict[str, str]:
        h = {"Accept": "application/json"}
        if self.settings.xui_api_token:
            h["Authorization"] = f"Bearer {self.settings.xui_api_token}"
        if self._cookie:
            h["Cookie"] = self._cookie
        return h

    async def _ensure_session(self, client: httpx.AsyncClient) -> bool:
        if self.settings.xui_api_token:
            return True
        if self._cookie:
            return True
        try:
            r = await client.post(
                f"{self.settings.xui_base_url.rstrip('/')}/login",
                data={
                    "username": self.settings.xui_username,
                    "password": self.settings.xui_password,
                },
                timeout=10.0,
            )
            if r.status_code == 200 and "session" in (r.headers.get("set-cookie") or "").lower():
                self._cookie = r.headers.get("set-cookie", "").split(";")[0]
                return True
            # some panels return JSON success
            try:
                body = r.json()
                if body.get("success"):
                    self._cookie = r.headers.get("set-cookie", "").split(";")[0]
                    return True
            except Exception:
                pass
            log.warning("3X-UI login failed status=%s (falling back to mock)", r.status_code)
            return False
        except Exception as e:
            log.warning("3X-UI unreachable (%s); using mock mode", type(e).__name__)
            return False

    async def _api(self, method: str, path: str, **kwargs: Any) -> Any | None:
        if self._use_mock:
            return None
        base = self.settings.xui_base_url.rstrip("/")
        url = f"{base}{path}"
        try:
            async with httpx.AsyncClient(follow_redirects=True, verify=False) as client:
                ok = await self._ensure_session(client)
                if not ok:
                    self._use_mock = True
                    return None
                r = await client.request(
                    method, url, headers=self._headers(), timeout=15.0, **kwargs
                )
                if r.status_code >= 400:
                    log.warning("3X-UI API %s %s -> %s", method, path, r.status_code)
                    return None
                return r.json()
        except Exception as e:
            log.warning("3X-UI API error %s; mock fallback", type(e).__name__)
            self._use_mock = True
            return None

    # ----- public ops -----

    async def get_client(self, email: str) -> ClientInfo | None:
        if self._use_mock:
            return _mock.clients.get(email)

        data = await self._api("GET", "/panel/api/inbounds/list")
        if data is None:
            return _mock.clients.get(email)
        try:
            for inbound in data.get("obj") or []:
                settings_raw = inbound.get("settings")
                import json

                settings = (
                    json.loads(settings_raw) if isinstance(settings_raw, str) else settings_raw
                ) or {}
                for c in settings.get("clients") or []:
                    if c.get("email") == email:
                        stats = self._find_client_stats(inbound, email)
                        online_set = await self._online_emails()
                        return ClientInfo(
                            email=email,
                            uuid=c.get("id") or "",
                            sub_id=c.get("subId") or "",
                            enable=bool(c.get("enable", True)),
                            total_bytes=int(c.get("totalGB") or 0) * (1024**3)
                            if c.get("totalGB") and int(c.get("totalGB") or 0) < 10_000
                            else int(c.get("totalGB") or 0),
                            up=int(stats.get("up") or 0),
                            down=int(stats.get("down") or 0),
                            expiry_ms=int(c.get("expiryTime") or 0),
                            limit_ip=int(c.get("limitIp") or 0),
                            online=email in online_set,
                            ips=[],
                        )
        except Exception as e:
            log.warning("parse inbounds failed: %s", type(e).__name__)
        return _mock.clients.get(email)

    def _find_client_stats(self, inbound: dict, email: str) -> dict:
        # clientStats may be on inbound
        for st in inbound.get("clientStats") or []:
            if st.get("email") == email:
                return st
        return {}

    async def _online_emails(self) -> set[str]:
        data = await self._api("POST", "/panel/api/inbounds/onlines")
        if not data:
            data = await self._api("POST", "/panel/api/clients/onlines")
        if not data:
            return set()
        obj = data.get("obj")
        if isinstance(obj, list):
            return set(str(x) for x in obj)
        return set()

    async def list_clients(self) -> list[ClientInfo]:
        if self._use_mock:
            return list(_mock.clients.values())
        # Prefer live list; fall back to mock keys only if unreachable
        data = await self._api("GET", "/panel/api/inbounds/list")
        if data is None:
            return list(_mock.clients.values())
        out: list[ClientInfo] = []
        for email in {c.email for c in _mock.clients.values()}:
            # still walk panel for known emails — full enumeration via inbound
            pass
        import json

        online_set = await self._online_emails()
        try:
            for inbound in data.get("obj") or []:
                settings_raw = inbound.get("settings")
                settings = (
                    json.loads(settings_raw) if isinstance(settings_raw, str) else settings_raw
                ) or {}
                for c in settings.get("clients") or []:
                    email = c.get("email") or ""
                    stats = self._find_client_stats(inbound, email)
                    total = c.get("totalGB") or 0
                    try:
                        total_i = int(total)
                    except Exception:
                        total_i = 0
                    # 3X-UI sometimes stores GB, sometimes bytes
                    total_bytes = total_i * (1024**3) if total_i < 10_000 else total_i
                    out.append(
                        ClientInfo(
                            email=email,
                            uuid=c.get("id") or "",
                            sub_id=c.get("subId") or "",
                            enable=bool(c.get("enable", True)),
                            total_bytes=total_bytes,
                            up=int(stats.get("up") or 0),
                            down=int(stats.get("down") or 0),
                            expiry_ms=int(c.get("expiryTime") or 0),
                            limit_ip=int(c.get("limitIp") or 0),
                            online=email in online_set,
                        )
                    )
        except Exception as e:
            log.warning("list_clients parse: %s", type(e).__name__)
            return list(_mock.clients.values())
        return out

    async def create_client(
        self,
        email: str,
        total_gb: int = 50,
        limit_ip: int = 2,
        expiry_ms: int = 0,
    ) -> ClientInfo:
        uid = str(uuid.uuid4())
        sub = secrets.token_hex(16)
        info = ClientInfo(
            email=email,
            uuid=uid,
            sub_id=sub,
            enable=True,
            total_bytes=total_gb * (1024**3),
            limit_ip=limit_ip,
            expiry_ms=expiry_ms,
        )
        if self._use_mock:
            _mock.clients[email] = info
            return info

        payload = {
            "id": self.settings.xui_inbound_id,
            "settings": (
                '{"clients":[{'
                f'"id":"{uid}","email":"{email}","enable":true,'
                f'"totalGB":{total_gb * (1024**3)},"expiryTime":{expiry_ms},'
                f'"limitIp":{limit_ip},"subId":"{sub}",'
                '"flow":"xtls-rprx-vision","reset":0'
                "}]}"
            ),
        }
        data = await self._api("POST", "/panel/api/inbounds/addClient", json=payload)
        if data is None or not data.get("success", True):
            # mock fallback so portal still works
            self._use_mock = True
            _mock.clients[email] = info
            log.warning("create_client fell back to mock for email=%s", email)
        else:
            _mock.clients[email] = info  # cache
        return info

    async def set_enable(self, email: str, enable: bool) -> bool:
        if self._use_mock or email in _mock.clients:
            if email in _mock.clients:
                _mock.clients[email].enable = enable
            if self._use_mock:
                return True

        # Try update by email
        data = await self._api(
            "POST",
            f"/panel/api/inbounds/updateClient/",
            # path variants differ by panel version; also try clients/update
        )
        data = await self._api(
            "POST",
            f"/panel/api/clients/update/{email}",
            json={"enable": enable},
        )
        if data and data.get("success"):
            if email in _mock.clients:
                _mock.clients[email].enable = enable
            return True
        # still update local mirror
        if email in _mock.clients:
            _mock.clients[email].enable = enable
        return True

    async def update_quota(self, email: str, total_gb: int, limit_ip: int | None = None) -> bool:
        if email in _mock.clients:
            _mock.clients[email].total_bytes = total_gb * (1024**3)
            if limit_ip is not None:
                _mock.clients[email].limit_ip = limit_ip
        if self._use_mock:
            return True
        body: dict[str, Any] = {"totalGB": total_gb * (1024**3)}
        if limit_ip is not None:
            body["limitIp"] = limit_ip
        data = await self._api("POST", f"/panel/api/clients/update/{email}", json=body)
        return bool(data and data.get("success", True))

    async def reset_sub_id(self, email: str) -> str | None:
        """Rotate subscription token (subId). Returns new sub_id; never log full URL."""
        new_sub = secrets.token_hex(16)
        if email in _mock.clients:
            _mock.clients[email].sub_id = new_sub
        if self._use_mock:
            return new_sub
        data = await self._api(
            "POST",
            f"/panel/api/clients/update/{email}",
            json={"subId": new_sub},
        )
        if data is None:
            self._use_mock = True
        return new_sub

    async def get_client_ips(self, email: str) -> list[str]:
        """Device/IP list if API allows; mock returns sample IPs."""
        if self._use_mock:
            c = _mock.clients.get(email)
            return list(c.ips) if c else []
        # 3X-UI may expose via client IP limit DB; try common endpoints
        data = await self._api("POST", f"/panel/api/inbounds/clientIps/{email}")
        if not data:
            data = await self._api("GET", f"/panel/api/inbounds/clientIps/{email}")
        if data and isinstance(data.get("obj"), str):
            # sometimes comma/newline separated
            raw = data["obj"].replace(",", "\n")
            return [x.strip() for x in raw.splitlines() if x.strip()]
        if data and isinstance(data.get("obj"), list):
            return [str(x) for x in data["obj"]]
        c = _mock.clients.get(email)
        return list(c.ips) if c else []


_xui: XUIClient | None = None


def get_xui() -> XUIClient:
    global _xui
    if _xui is None:
        _xui = XUIClient()
    return _xui
