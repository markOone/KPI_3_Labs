from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.commands.user_commands import AddUserCommand, LoginUserCommand
from src.application.commands.user_handlers import (
    AddUserCommandHandler,
    LoginUserCommandHandler,
)
from src.application.queries.user_handlers import GetUserQueryHandler
from src.application.queries.user_queries import GetUserQuery
from src.domain.repositories.repositories import UserRepository
from src.database.engine import db_helper
from src.infrastructure.repositories.user_repository import UserRepositoryImpl
from src.application.use_cases.auth_use_cases import RegisterUserUseCase
from src.domain.errors.domain_errors import (
    CredentialsError,
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
)
from src.config.dependencies import (
    get_current_user,
    get_jwt_manager,
    get_user_repository,
)
from src.schemas.auth import TokenResponse, UserResponseSchema

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    command: AddUserCommand,
    user_repo: UserRepositoryImpl = Depends(get_user_repository),
):
    handler = AddUserCommandHandler(user_repo)
    try:
        user_id = await handler.handle(command)
        return {"id": user_id}
    except (EmailAlreadyExistsError, UsernameAlreadyExistsError) as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    data: OAuth2PasswordRequestForm = Depends(),
    user_repo: UserRepositoryImpl = Depends(get_user_repository),
    jwt_manager=Depends(get_jwt_manager),
):
    command = LoginUserCommand(username=data.username, password=data.password)
    handler = LoginUserCommandHandler(user_repo)

    try:
        user = await handler.handle(command)
    except CredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    except Exception as e:
        print(f"Unexpected error during login: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error",
        )

    payload = {
        "sub": str(user.id),
        "username": user.username,
    }

    return {
        "access_token": jwt_manager.create_access_token(data=payload),
        "refresh_token": jwt_manager.create_refresh_token(data=payload),
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponseSchema)
async def get_me(user: int = Depends(get_current_user)):
    return user
