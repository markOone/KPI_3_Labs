from src.domain.entities.entities import Cart
from src.domain.repositories.repositories import CartRepository
from src.domain.errors.domain_errors import DomainError


class GetCartUseCase:
    """Use case for getting a user's cart"""

    def __init__(self, cart_repository: CartRepository):
        self.cart_repository = cart_repository

    async def execute(self, user_id: int) -> Cart:
        """Get cart for user"""
        cart = await self.cart_repository.get_by_user_id(user_id)
        if not cart:
            raise DomainError(f"Cart not found for user {user_id}")
        return cart


class AddToCartUseCase:
    """Use case for adding item to cart"""

    def __init__(self, cart_repository: CartRepository):
        self.cart_repository = cart_repository

    async def execute(self, user_id: int, product_id: int, quantity: float, price: float) -> Cart:
        """Add item to cart"""
        from src.domain.value_objects.value_objects import Quantity, Money

        cart = await self.cart_repository.get_by_user_id(user_id)
        if not cart:
            raise DomainError(f"Cart not found for user {user_id}")

        cart.add_item(
            product_id=product_id,
            quantity=Quantity(quantity),
            price=Money(price)
        )
        return await self.cart_repository.update(cart)


class RemoveFromCartUseCase:
    """Use case for removing item from cart"""

    def __init__(self, cart_repository: CartRepository):
        self.cart_repository = cart_repository

    async def execute(self, user_id: int, product_id: int) -> Cart:
        """Remove item from cart"""
        cart = await self.cart_repository.get_by_user_id(user_id)
        if not cart:
            raise DomainError(f"Cart not found for user {user_id}")

        cart.remove_item(product_id)
        return await self.cart_repository.update(cart)


class ClearCartUseCase:
    """Use case for clearing cart"""

    def __init__(self, cart_repository: CartRepository):
        self.cart_repository = cart_repository

    async def execute(self, user_id: int) -> Cart:
        """Clear all items from cart"""
        cart = await self.cart_repository.get_by_user_id(user_id)
        if not cart:
            raise DomainError(f"Cart not found for user {user_id}")

        cart.clear()
        return await self.cart_repository.update(cart)
