from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domain.entities.entities import User
from src.domain.repositories.repositories import UserRepository
from src.infrastructure.database.models import UserModel
from src.infrastructure.mappers.mappers import UserMapper


class UserRepositoryImpl(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> Optional[User]:
        query = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(query)
        orm_user = result.scalar_one_or_none()
        return UserMapper.from_orm(orm_user) if orm_user else None

    async def get_by_email(self, email: str) -> Optional[User]:
        query = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(query)
        orm_user = result.scalar_one_or_none()
        return UserMapper.from_orm(orm_user) if orm_user else None

    async def get_by_username(self, username: str) -> Optional[User]:
        query = select(UserModel).where(UserModel.username == username)
        result = await self.session.execute(query)
        orm_user = result.scalar_one_or_none()
        return UserMapper.from_orm(orm_user) if orm_user else None

    async def create(self, user: User) -> User:
        orm_user = UserModel(
            email=user.email.value,
            username=user.username,
            password_hash=user.password_hash,
            group_id=user.group_id
        )
        self.session.add(orm_user)
        await self.session.flush()
        user.id = orm_user.id
        return user

    async def update(self, user: User) -> User:
        query = select(UserModel).where(UserModel.id == user.id)
        result = await self.session.execute(query)
        orm_user = result.scalar_one_or_none()

        if orm_user:
            orm_user.email = user.email.value
            orm_user.username = user.username
            orm_user.password_hash = user.password_hash
            orm_user.group_id = user.group_id
            await self.session.flush()

        return user
