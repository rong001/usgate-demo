"""Display helpers — never log subscription URLs."""


def format_bytes(n: int) -> str:
    if n < 0:
        return "∞"
    units = ["B", "KB", "MB", "GB", "TB"]
    v = float(n)
    for u in units:
        if v < 1024 or u == units[-1]:
            if u == "B":
                return f"{int(v)} {u}"
            return f"{v:.2f} {u}"
        v /= 1024
    return f"{n} B"


def format_expiry(ms: int) -> str:
    if not ms or ms <= 0:
        return "Never / 永不过期"
    from datetime import datetime, timezone

    try:
        dt = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return "—"
