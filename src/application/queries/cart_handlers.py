from src.application.queries.cart_queries import GetCartQuery
from src.domain.entities.entities import Cart
from src.domain.repositories.repositories import CartRepository
from src.domain.errors.domain_errors import DomainError


class GetCartQueryHandler:
    def __init__(self, repo: CartRepository):
        self.repo = repo

    async def handle(self, query: GetCartQuery) -> Cart:
        cart = await self.repo.get_by_user_id(query.user_id)
        if not cart:
            raise DomainError(f"Cart not found for user {query.user_id}")
        return cart
