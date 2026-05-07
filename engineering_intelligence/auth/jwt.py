"""JWT token creation and validation."""

from datetime import datetime, timedelta, timezone

import jwt as pyjwt

from engineering_intelligence.config import get_settings


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode["exp"] = expire
    return pyjwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = pyjwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload
    except pyjwt.PyJWTError as e:
        raise ValueError(f"Invalid token: {e}") from e
