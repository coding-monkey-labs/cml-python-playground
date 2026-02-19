"""Pydantic schemas for Authentication API."""

from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    """Schema for token request (login)."""

    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    role: str = Field(default="client", pattern="^(admin|client)$")
    allowed_namespaces: list[str] | None = None


class APIKeyResponse(BaseModel):
    """Schema for API key response (only shown once on creation)."""

    key: str
    name: str
    role: str

    model_config = {"from_attributes": True}
