from src.domain.entities.entities import User
from src.domain.value_objects.value_objects import Email
from src.domain.repositories.repositories import UserRepository
from src.domain.errors.domain_errors import (
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
)
from src.auth.hashing import Hasher


class RegisterUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, username: str, email: str, password_plain: str) -> User:
        existing_email = await self.user_repo.get_by_email(email)
        if existing_email:
            raise EmailAlreadyExistsError("Користувач з таким email вже існує")

        existing_username = await self.user_repo.get_by_username(username)
        if existing_username:
            raise UsernameAlreadyExistsError("Користувач з таким username вже існує")

        user = User(
            id=0,
            username=username,
            email=Email(email),
            password_hash=Hasher.get_password_hash(password_plain),
            group_id=2,
        )
        new_user = await self.user_repo.create(user)
        return new_user.id


class LoginUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, username: str, password_plain: str) -> User:
        user = await self.user_repo.get_by_username(username)
        if not user or not Hasher.verify_password(password_plain, user.password_hash):
            raise ValueError("Невірний username або пароль")
        return user
