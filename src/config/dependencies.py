from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.application.queries.user_handlers import GetUserQueryHandler
from src.application.queries.user_queries import GetUserQuery
from src.domain.repositories.repositories import UserRepository
from src.infrastructure.repositories.user_repository import UserRepositoryImpl
from src.config.settings import settings, AppSettings
from src.database.models import User
from src.database.engine import db_helper
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.services import JWTManager
from jose import JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_user_repository(db: AsyncSession = Depends(db_helper.get_db_session)):
    return UserRepositoryImpl(db)


async def get_settings() -> AppSettings:
    return settings


async def get_jwt_manager(settings: AppSettings = Depends(get_settings)) -> JWTManager:
    return JWTManager(
        secret_key=settings.auth.secret_key,
        algorithm=settings.auth.algorithm,
        access_token_expire_minutes=settings.auth.access_token_expire_minutes,
        refresh_token_expire_days=settings.auth.refresh_token_expire_days,
    )


async def get_user_by_name(username, db):
    result = await db.execute(
        select(User).where(User.username == username).options(selectinload(User.group))
    )
    return result.scalar_one_or_none()


async def get_current_user_id(
    token: str = Depends(oauth2_scheme),
    jwt_manager=Depends(get_jwt_manager),
) -> int:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt_manager.decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return int(user_id)
    except (JWTError, ValueError):
        raise credentials_exception


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    try:
        query = GetUserQuery(user_id=user_id)
        handler = GetUserQueryHandler(user_repo)
        return await handler.handle(query)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )


async def require_admin(
    user_id: int = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    query = GetUserQuery(user_id=user_id)
    handler = GetUserQueryHandler(user_repo)

    try:
        user_dto = await handler.handle(query)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    if user_dto.group_name != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return user_dto
