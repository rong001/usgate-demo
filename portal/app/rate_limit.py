"""In-memory sliding-window rate limiter for login."""
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request

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


def check_login_rate(request: Request) -> None:
    s = get_settings()
    key = f"login:{client_ip(request)}"
    now = time.monotonic()
    window = float(s.login_rate_window_seconds)
    limit = s.login_rate_limit

    with _lock:
        q = _buckets[key]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(
                status_code=429,
                detail=f"Too many login attempts. Try again in {int(window)}s.",
            )
        q.append(now)
