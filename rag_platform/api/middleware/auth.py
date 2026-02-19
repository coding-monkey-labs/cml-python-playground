"""Authentication middleware - JWT and API Key support."""

import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, APIKeyHeader
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_platform.core.config import get_settings
from rag_platform.db.models.api_key import APIKey
from rag_platform.db.session import get_db

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name=settings.api_key_header, auto_error=False)


def create_access_token(subject: str, role: str = "admin") -> dict:
    """Create a JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    payload = {
        "sub": subject,
        "role": role,
        "exp": expire,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.jwt_access_token_expire_minutes * 60,
    }


def verify_jwt_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def hash_api_key(key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


async def get_current_user(
    bearer: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    api_key: str | None = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Authenticate via JWT bearer token or API key.

    Returns a dict with 'subject' and 'role' keys.
    """
    # Try JWT first
    if bearer and bearer.credentials:
        payload = verify_jwt_token(bearer.credentials)
        return {"subject": payload.get("sub"), "role": payload.get("role", "client")}

    # Try API key
    if api_key:
        key_hash = hash_api_key(api_key)
        result = await db.execute(
            select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active.is_(True))
        )
        db_key = result.scalar_one_or_none()
        if db_key:
            # Check expiration
            if db_key.expires_at and db_key.expires_at < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key has expired",
                )
            # Update last used
            db_key.last_used_at = datetime.now(timezone.utc)
            await db.flush()
            return {"subject": db_key.name, "role": db_key.role}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Require admin role."""
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
