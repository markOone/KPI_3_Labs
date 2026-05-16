import logging
from email_validator import validate_email, EmailNotValidError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.auth.hashing import Hasher
from src.config.dependencies import get_current_user, get_jwt_manager
from src.schemas.auth import (
    TokenResponse,
    UserRegisterSchema,
    UserResponseSchema,
)
from src.database.engine import db_helper
from src.database.models import User

router = APIRouter(prefix="/auth", tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegisterSchema, db: AsyncSession = Depends(db_helper.get_db_session)
):
    try:
        validate_email(data.email, check_deliverability=False)
    except EmailNotValidError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid email: {str(e)}"
        )

    query = select(User).where(User.email == data.email)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )

    try:
        new_user = User(
            username=data.username,
            email=data.email,
            password_hash=Hasher.get_password_hash(data.password),
            group_id=2,  # default to regular user group
        )
        db.add(new_user)
        await db.commit()
        return {"status": "success"}
    except Exception as e:
        await db.rollback()
        logging.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(db_helper.get_db_session),
    jwt_manager=Depends(get_jwt_manager),
):
    try:
        result = await db.execute(select(User).where(User.username == data.username))
        user = result.scalar_one_or_none()

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
    except Exception as e:
        logging.error(f"Error during login: {e}")
        raise HTTPException(status_code=400, detail="Login failed")


@router.get("/me", response_model=UserResponseSchema)
async def read_users_me(
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return current_user
