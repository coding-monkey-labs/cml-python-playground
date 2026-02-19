"""Authentication routes."""

import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from rag_platform.api.middleware.auth import (
    create_access_token,
    hash_api_key,
    require_admin,
)
from rag_platform.core.config import get_settings
from rag_platform.db.models.api_key import APIKey
from rag_platform.db.session import get_db
from rag_platform.schemas.auth import APIKeyCreate, APIKeyResponse, TokenRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()

# Simple admin credentials for Phase 1 (move to DB in Phase 2)
ADMIN_USERS = {
    "admin": "admin",  # Change in production
}


@router.post("/token", response_model=TokenResponse)
async def login(request: TokenRequest):
    """Authenticate and receive a JWT token."""
    if request.username not in ADMIN_USERS or ADMIN_USERS[request.username] != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token_data = create_access_token(subject=request.username, role="admin")
    return TokenResponse(**token_data)


@router.post("/api-key", response_model=APIKeyResponse)
async def create_api_key(
    request: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_admin),
):
    """Create a new API key (admin only). The key is only shown once."""
    raw_key = f"rag_{secrets.token_urlsafe(32)}"
    key_hash = hash_api_key(raw_key)

    db_key = APIKey(
        key_hash=key_hash,
        name=request.name,
        description=request.description,
        role=request.role,
        allowed_namespaces=",".join(request.allowed_namespaces) if request.allowed_namespaces else None,
    )
    db.add(db_key)
    await db.flush()

    return APIKeyResponse(key=raw_key, name=db_key.name, role=db_key.role)
