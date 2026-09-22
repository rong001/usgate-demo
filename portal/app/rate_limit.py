"""In-memory sliding-window rate limiters (login + optional global)."""
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.config import get_settings

_lock = Lock()
_buckets: dict[str, deque[float]] = defaultdict(deque)


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _check(key: str, limit: int, window: float) -> None:
    if limit <= 0:
        return
    now = time.monotonic()
    with _lock:
        q = _buckets[key]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(
                status_code=429,
                detail=f"Too many requests. Try again in {int(window)}s.",
            )
        q.append(now)


def check_login_rate(request: Request) -> None:
    s = get_settings()
    _check(
        f"login:{client_ip(request)}",
        s.login_rate_limit,
        float(s.login_rate_window_seconds),
    )


def check_global_rate(request: Request) -> None:
    s = get_settings()
    _check(
        f"global:{client_ip(request)}",
        s.global_rate_limit,
        float(s.global_rate_window_seconds),
    )


def reset_rate_buckets() -> None:
    """Test / demo-reset helper."""
    with _lock:
        _buckets.clear()


class GlobalRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip static + healthz from global budget
        path = request.url.path
        if path.startswith("/static") or path == "/healthz":
            return await call_next(request)
        try:
            check_global_rate(request)
        except HTTPException as exc:
            return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
        return await call_next(request)
