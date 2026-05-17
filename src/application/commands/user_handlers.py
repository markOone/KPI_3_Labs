from src.domain.errors.domain_errors import (
    CredentialsError,
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
)
from src.application.commands.user_commands import (
    AddUserCommand,
    LoginUserCommand,
)
from src.schemas.auth import UserResponseSchema
from src.auth.hashing import Hasher
from src.domain.entities.entities import User
from src.domain.repositories.repositories import UserRepository
from src.domain.value_objects.value_objects import Email


class AddUserCommandHandler:
    # """Handler for AddUserCommand"""
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def handle(self, command: AddUserCommand) -> int:

        if await self.repo.get_by_username(command.username):
            raise UsernameAlreadyExistsError(
                f"User '{command.username}' already exists"
            )

        if await self.repo.get_by_email(command.email):
            raise EmailAlreadyExistsError(f"Email '{command.email}' already registered")

        user = User(
            id=0,
            email=Email(command.email),
            username=command.username,
            password_hash=Hasher.get_password_hash(command.password),
        )
        await self.repo.create(user)
        return user.id


class LoginUserCommandHandler:
    # """Handler for LoginUserCommand"""
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def handle(self, command: LoginUserCommand) -> UserResponseSchema:
        user = await self.repo.get_by_username(command.username)
        if not user or not Hasher.verify_password(command.password, user.password_hash):
            raise CredentialsError("Invalid email or password")
        return UserResponseSchema(
            id=user.id,
            username=user.username,
            email=user.email.value,
            group_id=user.group_id,
        )
