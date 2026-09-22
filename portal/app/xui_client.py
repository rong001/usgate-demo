"""
3X-UI panel API client with switchable mock mode.

Single switch: MOCK_XUI=true|false (see app.config / env.example).
When MOCK_XUI=false, live failures raise XUIError — no silent mock fallback
unless MOCK_XUI_FALLBACK=true (explicit, default OFF).

NEVER log full subscription URLs, passwords, cookies, or UUIDs (mask_* helpers).

Real adapter maps to common 3X-UI panel API paths (MHSanaei / similar forks):
  POST /login                                      — session cookie auth
  GET  /panel/api/inbounds/list                    — list inbounds + clients
  POST /panel/api/inbounds/addClient               — create client on inbound
  POST /panel/api/inbounds/updateClient/{uuid}     — update by client UUID
  POST /panel/api/inbounds/onlines                 — online client emails
  POST /panel/api/inbounds/clientIps/{email}       — device IPs
  POST /panel/api/inbounds/clearClientIps/{email}  — clear IPs
"""
from __future__ import annotations

import json
import logging
import secrets
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.config import get_settings

log = logging.getLogger("usgate.xui")


# ---------- masking (never log secrets) ----------

def mask_url(url: str, keep: int = 8) -> str:
    """Mask middle of URL for display; never log the full URL."""
    if not url:
        return "****"
    if len(url) <= keep * 2 + 3:
        return url[:4] + "…" + url[-4:] if len(url) > 8 else "****"
    return url[:keep] + "…" + url[-keep:]


def mask_secret(value: str | None, keep: int = 4) -> str:
    """Mask UUID / token / cookie / password-like strings for logs."""
    if not value:
        return "****"
    v = str(value)
    if len(v) <= keep * 2:
        return "****"
    return v[:keep] + "…" + v[-keep:]


# ---------- errors ----------

class XUIError(Exception):
    """Structured panel/adapter failure (no silent swallow in live mode)."""

    def __init__(self, code: str, message: str, *, http_status: int | None = None):
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(f"{code}: {message}")

    def as_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"error": self.code, "message": self.message}
        if self.http_status is not None:
            d["http_status"] = self.http_status
        return d


# ---------- data ----------

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
    inbound_id: int | None = None

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


def _total_to_bytes(raw: Any) -> int:
    """3X-UI may store totalGB as GB or as bytes depending on version."""
    try:
        n = int(raw or 0)
    except (TypeError, ValueError):
        return 0
    if n <= 0:
        return 0
    return n * (1024**3) if n < 10_000 else n


# ---------- Mock store ----------

class _MockStore:
    def __init__(self) -> None:
        self.clients: dict[str, ClientInfo] = {}
        self._seed()

    def _seed(self) -> None:
        self.clients.clear()
        demo = [
            ("demo-admin", 200 * 1024**3, 3, True),
            ("demo-user1", 50 * 1024**3, 2, False),
        ]
        for email, total, lim, online in demo:
            uid = str(uuid.uuid4())
            sub = secrets.token_hex(16)
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

    def reset(self) -> None:
        """Reseed synthetic clients (MOCK demo only)."""
        self._seed()


_mock = _MockStore()


def reset_mock_store() -> None:
    """Public hook for demo-reset / E2E (MOCK only)."""
    _mock.reset()


def get_mock_store() -> _MockStore:
    return _mock


# ---------- Client ----------

class XUIClient:
    """Talks to 3X-UI when MOCK_XUI=false; otherwise pure in-memory mock."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._cookie: str | None = None
        # Bound at construction from MOCK_XUI — do not flip silently
        self._use_mock = bool(self.settings.mock_xui)
        self._allow_fallback = bool(self.settings.mock_xui_fallback)

    @property
    def is_mock(self) -> bool:
        return self._use_mock

    def _headers(self) -> dict[str, str]:
        h = {"Accept": "application/json"}
        if self.settings.xui_api_token:
            # Token auth variant (some forks); never log the token
            h["Authorization"] = f"Bearer {self.settings.xui_api_token}"
        if self._cookie:
            h["Cookie"] = self._cookie
        return h

    def _maybe_fallback(self, err: XUIError) -> None:
        """In live mode: raise unless MOCK_XUI_FALLBACK=true."""
        if self.settings.mock_xui:
            return
        if self._allow_fallback:
            log.warning(
                "3X-UI error %s — MOCK_XUI_FALLBACK=true, switching to mock",
                err.code,
            )
            self._use_mock = True
            return
        raise err

    async def _ensure_session(self, client: httpx.AsyncClient) -> None:
        """
        Establish panel session.
        Paths: POST {XUI_BASE_URL}/login  (form: username, password)
        Prefer XUI_API_TOKEN when set (no password login).
        """
        if self.settings.xui_api_token:
            return
        if self._cookie:
            return
        try:
            r = await client.post(
                f"{self.settings.xui_base_url.rstrip('/')}/login",
                data={
                    "username": self.settings.xui_username,
                    "password": self.settings.xui_password,
                },
                timeout=10.0,
            )
        except Exception as e:
            raise XUIError(
                "xui_unreachable",
                f"panel login transport failed: {type(e).__name__}",
            ) from e

        set_cookie = r.headers.get("set-cookie") or ""
        # Never log cookie or password
        if r.status_code == 200 and "session" in set_cookie.lower():
            self._cookie = set_cookie.split(";")[0]
            log.info("3X-UI session established (cookie=%s)", mask_secret(self._cookie))
            return
        try:
            body = r.json()
            if body.get("success"):
                self._cookie = set_cookie.split(";")[0] if set_cookie else self._cookie
                if self._cookie:
                    log.info(
                        "3X-UI session established via JSON success (cookie=%s)",
                        mask_secret(self._cookie),
                    )
                    return
        except Exception:
            pass
        raise XUIError(
            "xui_login_failed",
            f"panel login rejected status={r.status_code}",
            http_status=r.status_code,
        )

    async def _api(self, method: str, path: str, **kwargs: Any) -> Any:
        """
        Low-level JSON API call. Raises XUIError on failure in live mode.
        path examples: /panel/api/inbounds/list
        """
        if self._use_mock:
            raise XUIError("mock_mode", "API called while MOCK_XUI=true")

        base = self.settings.xui_base_url.rstrip("/")
        url = f"{base}{path}"
        try:
            async with httpx.AsyncClient(follow_redirects=True, verify=False) as client:
                await self._ensure_session(client)
                r = await client.request(
                    method, url, headers=self._headers(), timeout=15.0, **kwargs
                )
        except XUIError:
            raise
        except Exception as e:
            raise XUIError(
                "xui_api_transport",
                f"{method} {path} failed: {type(e).__name__}",
            ) from e

        if r.status_code >= 400:
            raise XUIError(
                "xui_api_http",
                f"{method} {path} -> HTTP {r.status_code}",
                http_status=r.status_code,
            )
        try:
            return r.json()
        except Exception as e:
            raise XUIError(
                "xui_api_parse",
                f"{method} {path} non-JSON response",
            ) from e

    def _parse_client_from_inbound(
        self, inbound: dict, c: dict, online_set: set[str]
    ) -> ClientInfo:
        email = c.get("email") or ""
        stats = self._find_client_stats(inbound, email)
        return ClientInfo(
            email=email,
            uuid=c.get("id") or "",
            sub_id=c.get("subId") or "",
            enable=bool(c.get("enable", True)),
            total_bytes=_total_to_bytes(c.get("totalGB")),
            up=int(stats.get("up") or 0),
            down=int(stats.get("down") or 0),
            expiry_ms=int(c.get("expiryTime") or 0),
            limit_ip=int(c.get("limitIp") or 0),
            online=email in online_set,
            inbound_id=int(inbound.get("id") or 0) or None,
            ips=[],
        )

    def _find_client_stats(self, inbound: dict, email: str) -> dict:
        for st in inbound.get("clientStats") or []:
            if st.get("email") == email:
                return st
        return {}

    def _iter_clients(self, data: Any) -> list[tuple[dict, dict]]:
        """Yield (inbound, client_dict) from inbounds/list response."""
        out: list[tuple[dict, dict]] = []
        for inbound in (data.get("obj") or []) if isinstance(data, dict) else []:
            settings_raw = inbound.get("settings")
            try:
                settings = (
                    json.loads(settings_raw)
                    if isinstance(settings_raw, str)
                    else settings_raw
                ) or {}
            except Exception:
                settings = {}
            for c in settings.get("clients") or []:
                out.append((inbound, c))
        return out

    async def _online_emails(self) -> set[str]:
        # POST /panel/api/inbounds/onlines — returns list of online emails
        try:
            data = await self._api("POST", "/panel/api/inbounds/onlines")
        except XUIError:
            try:
                data = await self._api("POST", "/panel/api/clients/onlines")
            except XUIError:
                return set()
        obj = data.get("obj") if isinstance(data, dict) else None
        if isinstance(obj, list):
            return set(str(x) for x in obj)
        return set()

    async def _find_live_client(self, email: str) -> tuple[dict, dict, ClientInfo] | None:
        """Return (inbound, raw_client, ClientInfo) for email or None."""
        data = await self._api("GET", "/panel/api/inbounds/list")
        online_set = await self._online_emails()
        for inbound, c in self._iter_clients(data):
            if c.get("email") == email:
                info = self._parse_client_from_inbound(inbound, c, online_set)
                return inbound, c, info
        return None

    # ----- public ops -----

    async def get_client(self, email: str) -> ClientInfo | None:
        if self._use_mock:
            return _mock.clients.get(email)

        try:
            found = await self._find_live_client(email)
            return found[2] if found else None
        except XUIError as e:
            self._maybe_fallback(e)
            if self._use_mock:
                return _mock.clients.get(email)
            raise

    async def list_clients(self) -> list[ClientInfo]:
        if self._use_mock:
            return list(_mock.clients.values())

        try:
            data = await self._api("GET", "/panel/api/inbounds/list")
            online_set = await self._online_emails()
            out: list[ClientInfo] = []
            for inbound, c in self._iter_clients(data):
                out.append(self._parse_client_from_inbound(inbound, c, online_set))
            return out
        except XUIError as e:
            self._maybe_fallback(e)
            if self._use_mock:
                return list(_mock.clients.values())
            raise

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
            inbound_id=self.settings.xui_inbound_id,
        )
        if self._use_mock:
            _mock.clients[email] = info
            log.info("mock create_client email=%s uuid=%s", email, mask_secret(uid))
            return info

        # POST /panel/api/inbounds/addClient
        # settings is a JSON *string* with clients array (3X-UI convention)
        client_obj = {
            "id": uid,
            "email": email,
            "enable": True,
            "totalGB": total_gb * (1024**3),
            "expiryTime": expiry_ms,
            "limitIp": limit_ip,
            "subId": sub,
            "flow": "xtls-rprx-vision",
            "reset": 0,
        }
        payload = {
            "id": self.settings.xui_inbound_id,
            "settings": json.dumps({"clients": [client_obj]}),
        }
        try:
            data = await self._api("POST", "/panel/api/inbounds/addClient", json=payload)
            if not isinstance(data, dict) or data.get("success") is False:
                raise XUIError(
                    "xui_create_failed",
                    f"addClient unsuccessful for email={email}",
                )
            log.info("live create_client email=%s uuid=%s", email, mask_secret(uid))
            return info
        except XUIError as e:
            self._maybe_fallback(e)
            if self._use_mock:
                _mock.clients[email] = info
                return info
            raise

    async def set_enable(self, email: str, enable: bool) -> bool:
        if self._use_mock:
            if email in _mock.clients:
                _mock.clients[email].enable = enable
            return True

        try:
            found = await self._find_live_client(email)
            if not found:
                raise XUIError("xui_client_not_found", f"no panel client email={email}")
            inbound, raw, info = found
            raw = dict(raw)
            raw["enable"] = enable
            # POST /panel/api/inbounds/updateClient/{clientUUID}
            payload = {
                "id": inbound.get("id") or self.settings.xui_inbound_id,
                "settings": json.dumps({"clients": [raw]}),
            }
            data = await self._api(
                "POST",
                f"/panel/api/inbounds/updateClient/{info.uuid}",
                json=payload,
            )
            if isinstance(data, dict) and data.get("success") is False:
                raise XUIError("xui_update_failed", f"enable={enable} email={email}")
            log.info(
                "live set_enable email=%s enable=%s uuid=%s",
                email,
                enable,
                mask_secret(info.uuid),
            )
            return True
        except XUIError as e:
            self._maybe_fallback(e)
            if self._use_mock:
                if email in _mock.clients:
                    _mock.clients[email].enable = enable
                return True
            raise

    async def update_quota(
        self, email: str, total_gb: int, limit_ip: int | None = None
    ) -> bool:
        if self._use_mock:
            if email in _mock.clients:
                _mock.clients[email].total_bytes = total_gb * (1024**3)
                if limit_ip is not None:
                    _mock.clients[email].limit_ip = limit_ip
            return True

        try:
            found = await self._find_live_client(email)
            if not found:
                raise XUIError("xui_client_not_found", f"no panel client email={email}")
            inbound, raw, info = found
            raw = dict(raw)
            raw["totalGB"] = total_gb * (1024**3)
            if limit_ip is not None:
                raw["limitIp"] = limit_ip
            payload = {
                "id": inbound.get("id") or self.settings.xui_inbound_id,
                "settings": json.dumps({"clients": [raw]}),
            }
            data = await self._api(
                "POST",
                f"/panel/api/inbounds/updateClient/{info.uuid}",
                json=payload,
            )
            if isinstance(data, dict) and data.get("success") is False:
                raise XUIError("xui_quota_failed", f"email={email}")
            return True
        except XUIError as e:
            self._maybe_fallback(e)
            if self._use_mock:
                if email in _mock.clients:
                    _mock.clients[email].total_bytes = total_gb * (1024**3)
                    if limit_ip is not None:
                        _mock.clients[email].limit_ip = limit_ip
                return True
            raise

    async def reset_sub_id(self, email: str) -> str | None:
        """Rotate subscription token (subId). Returns new sub_id; never log full URL."""
        new_sub = secrets.token_hex(16)
        if self._use_mock:
            if email in _mock.clients:
                _mock.clients[email].sub_id = new_sub
            log.info("mock reset_sub_id email=%s sub=%s", email, mask_secret(new_sub))
            return new_sub

        try:
            found = await self._find_live_client(email)
            if not found:
                raise XUIError("xui_client_not_found", f"no panel client email={email}")
            inbound, raw, info = found
            raw = dict(raw)
            raw["subId"] = new_sub
            payload = {
                "id": inbound.get("id") or self.settings.xui_inbound_id,
                "settings": json.dumps({"clients": [raw]}),
            }
            data = await self._api(
                "POST",
                f"/panel/api/inbounds/updateClient/{info.uuid}",
                json=payload,
            )
            if isinstance(data, dict) and data.get("success") is False:
                raise XUIError("xui_reset_sub_failed", f"email={email}")
            log.info("live reset_sub_id email=%s sub=%s", email, mask_secret(new_sub))
            return new_sub
        except XUIError as e:
            self._maybe_fallback(e)
            if self._use_mock:
                if email in _mock.clients:
                    _mock.clients[email].sub_id = new_sub
                return new_sub
            raise

    async def get_client_ips(self, email: str) -> list[str]:
        """Device/IP list if API allows; mock returns sample IPs."""
        if self._use_mock:
            c = _mock.clients.get(email)
            return list(c.ips) if c else []

        try:
            # POST /panel/api/inbounds/clientIps/{email}
            try:
                data = await self._api(
                    "POST", f"/panel/api/inbounds/clientIps/{email}"
                )
            except XUIError:
                data = await self._api(
                    "GET", f"/panel/api/inbounds/clientIps/{email}"
                )
            if data and isinstance(data.get("obj"), str):
                raw = data["obj"].replace(",", "\n")
                return [x.strip() for x in raw.splitlines() if x.strip()]
            if data and isinstance(data.get("obj"), list):
                return [str(x) for x in data["obj"]]
            return []
        except XUIError as e:
            self._maybe_fallback(e)
            if self._use_mock:
                c = _mock.clients.get(email)
                return list(c.ips) if c else []
            raise

    async def clear_client_ips(self, email: str) -> bool:
        if self._use_mock:
            if email in _mock.clients:
                _mock.clients[email].ips = []
            return True
        try:
            # POST /panel/api/inbounds/clearClientIps/{email}
            await self._api("POST", f"/panel/api/inbounds/clearClientIps/{email}")
            return True
        except XUIError as e:
            self._maybe_fallback(e)
            if self._use_mock:
                if email in _mock.clients:
                    _mock.clients[email].ips = []
                return True
            raise


_xui: XUIClient | None = None


def get_xui() -> XUIClient:
    global _xui
    if _xui is None:
        _xui = XUIClient()
    return _xui


def reset_xui_singleton() -> None:
    """Clear singleton (tests / after settings change)."""
    global _xui
    _xui = None
