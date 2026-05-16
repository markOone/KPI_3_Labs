from src.domain.entities.entities import User
from src.domain.value_objects.value_objects import Email
from src.domain.repositories.repositories import UserRepository
from src.domain.errors.domain_errors import EmailAlreadyExistsError, UsernameAlreadyExistsError
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
            group_id=2
        )
        return await self.user_repo.create(user)