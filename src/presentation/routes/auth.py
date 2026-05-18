from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.engine import db_helper
from src.infrastructure.repositories.user_repository import UserRepositoryImpl
from src.application.use_cases.auth_use_cases import RegisterUserUseCase
from src.domain.errors.domain_errors import (
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
)
from src.config.dependencies import get_current_user, get_jwt_manager
from src.schemas.auth import TokenResponse, UserRegisterSchema, UserResponseSchema
from src.auth.hashing import Hasher

router = APIRouter(prefix="/auth", tags=["Auth"])


async def get_user_repository(db: AsyncSession = Depends(db_helper.get_db_session)):
    return UserRepositoryImpl(db)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegisterSchema,
    user_repo: UserRepositoryImpl = Depends(get_user_repository),
):
    use_case = RegisterUserUseCase(user_repo)
    try:
        await use_case.execute(
            username=data.username, email=data.email, password_plain=data.password
        )
        
        return {"status": "success"}
    except (EmailAlreadyExistsError, UsernameAlreadyExistsError) as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    data: OAuth2PasswordRequestForm = Depends(),
    user_repo: UserRepositoryImpl = Depends(get_user_repository),
    jwt_manager=Depends(get_jwt_manager),
):
    user = await user_repo.get_by_username(data.username)
    if not user or not Hasher.verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    payload = {"sub": str(user.id), "username": user.username}
    return {
        "access_token": jwt_manager.create_access_token(data=payload),
        "refresh_token": jwt_manager.create_refresh_token(data=payload),
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponseSchema)
async def read_users_me(current_user: UserResponseSchema = Depends(get_current_user)):
    return current_user
