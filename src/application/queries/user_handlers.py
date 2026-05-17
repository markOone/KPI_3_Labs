from src.application.queries.user_queries import GetUserQuery
from src.domain.repositories.repositories import UserRepository
from src.schemas.auth import UserResponseSchema


class GetUserQueryHandler:
    # """Handler for GetUserQuery"""
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def handle(self, query: GetUserQuery) -> UserResponseSchema:
        user = await self.repo.get_by_id(query.user_id)
        if not user:
            raise ValueError(f"User with ID {query.user_id} not found")

        return UserResponseSchema(
            id=user.id,
            username=user.username,
            email=user.email.value,
        )
