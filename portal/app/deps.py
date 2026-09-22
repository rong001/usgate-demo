"""Shared FastAPI dependencies."""
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_session
from app.database import get_db
from app.models import User


async def current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    sess = get_session(request)
    if not sess or "uid" not in sess:
        return None
    result = await db.execute(select(User).where(User.id == sess["uid"]))
    user = result.scalar_one_or_none()
    if user and not user.is_active and not user.is_admin:
        return None
    return user


async def require_user(
    user: Annotated[User | None, Depends(current_user)],
) -> User:
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user


async def require_admin(
    user: Annotated[User | None, Depends(current_user)],
) -> User:
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    return user


def redirect_login() -> RedirectResponse:
    return RedirectResponse("/login", status_code=303)
