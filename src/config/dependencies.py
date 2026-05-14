from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import text
from src.exceptions.token import InvalidTokenError
from src.config.settings import settings, AppSettings
from src.database.models import User
from src.database.engine import db_helper
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.services import JWTManager
from jose import JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_settings() -> AppSettings:
    return settings


async def get_jwt_manager(settings: AppSettings = Depends(get_settings)) -> JWTManager:
    return JWTManager(
        secret_key=settings.auth.secret_key,
        algorithm=settings.auth.algorithm,
        access_token_expire_minutes=settings.auth.access_token_expire_minutes,
        refresh_token_expire_days=settings.auth.refresh_token_expire_days,
    )

get_user_by_name = lambda db, username: db.execute(
    text("SELECT * FROM users WHERE username = :username"),
    {"username": username}
).fetchone()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(db_helper.get_db_session),
    jwt_manager: JWTManager = Depends(JWTManager),
    settings: AppSettings = Depends(get_settings),
) -> User:
    try:
        payload = jwt_manager.decode(
            token, settings.auth.secret_key, algorithms=[settings.auth.algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise InvalidTokenError
    except JWTError:
        raise InvalidTokenError
    user = await get_user_by_name(db, username=username)
    if user is None:
        raise InvalidTokenError
    return user