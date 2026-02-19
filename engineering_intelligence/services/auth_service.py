"""Authentication service."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from engineering_intelligence.auth.jwt import create_access_token
from engineering_intelligence.auth.password import hash_password, verify_password
from engineering_intelligence.db.models import User, UserRole
from engineering_intelligence.repositories.user_repo import UserRepository
from engineering_intelligence.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserResponse


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = UserRepository(db)

    async def login(self, request: LoginRequest) -> TokenResponse:
        user = await self._repo.get_by_email(request.email)
        if not user or not verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )
        token = create_access_token({"sub": user.email, "role": user.role.value})
        return TokenResponse(access_token=token)

    async def register(self, request: UserCreate) -> UserResponse:
        existing = await self._repo.get_by_email(request.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )
        user = User(
            email=request.email,
            hashed_password=hash_password(request.password),
            full_name=request.full_name,
            role=UserRole(request.role),
        )
        user = await self._repo.create(user)
        return UserResponse.model_validate(user)
