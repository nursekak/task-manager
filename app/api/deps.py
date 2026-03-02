from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.crud import get_user_by_email
from app.db import get_db
from app.models import User

security = HTTPBearer(auto_error=False)


def get_redis_client():
    import redis
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


def rate_limit_per_user(user_id: int, redis_client=None) -> None:
    """Raise 429 if user exceeded RATE_LIMIT_PER_MINUTE in current minute."""
    if redis_client is None:
        redis_client = get_redis_client()
    from datetime import datetime, timezone

    key = f"ratelimit:{user_id}:{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}"
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, 120)
    n, _ = pipe.execute()
    if n > settings.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later.",
        )


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    user = get_user_by_email(db, sub)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


def rate_limit_dep(
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    rate_limit_per_user(current_user.id)


def get_current_user_optional(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> User | None:
    if credentials is None:
        return None
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        return None
    sub = payload.get("sub")
    if not sub:
        return None
    return get_user_by_email(db, sub)
