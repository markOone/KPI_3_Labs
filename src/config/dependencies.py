from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from src.exceptions.token import InvalidTokenError
from src.config.settings import settings, AppSettings
from src.infrastructure.database.models import User
from src.infrastructure.repositories.stock_repository import StockRepositoryImpl
from src.infrastructure.engine import db_helper
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.services import JWTManager
from jose import JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_settings() -> AppSettings:
    return settings


async def get_stock_repository(db: AsyncSession = Depends(db_helper.get_db_session)):
    return StockRepositoryImpl(db)


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


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(db_helper.get_db_session),
    jwt_manager: JWTManager = Depends(get_jwt_manager),
) -> User:
    try:
        payload = jwt_manager.decode_access_token(token)
        # print(payload)
        username: str = payload.get("username")
        if username is None:
            raise InvalidTokenError("Token payload missing 'sub' field")
    except JWTError as e:
        raise InvalidTokenError(f"Token decode error: {e}")
    user = await get_user_by_name(username, db)
    if user is None:
        raise InvalidTokenError(f"User not found")
    # print(user)
    return user


async def require_admin(current_user: User = Depends(get_current_user)):
    # print(current_user.group.name)
    if current_user.group.name != "Admin":
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
