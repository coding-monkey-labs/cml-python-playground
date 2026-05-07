"""Auth router — login, register, token refresh."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from engineering_intelligence.auth.dependencies import get_current_user
from engineering_intelligence.db import get_db
from engineering_intelligence.db.models import User
from engineering_intelligence.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserResponse
from engineering_intelligence.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.login(request)


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(request: UserCreate, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.register(request)


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)
