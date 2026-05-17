from src.domain.entities.entities import Cart
from src.domain.repositories.repositories import CartRepository
from src.domain.errors.domain_errors import DomainError
from src.domain.value_objects.value_objects import Quantity, Money
from src.application.commands.cart_commands import (
    AddToCartCommand,
    RemoveFromCartCommand,
    ClearCartCommand,
)


class AddToCartCommandHandler:
    # """Handler for adding items to the cart"""
    def __init__(self, repo: CartRepository):
        self.repo = repo

    async def handle(self, command: AddToCartCommand) -> Cart:
        cart = await self.repo.get_by_user_id(command.user_id)
        if not cart:
            raise DomainError(f"Cart not found for user {command.user_id}")

        cart.add_item(
            product_id=command.product_id,
            quantity=Quantity(command.quantity),
        )
        return await self.repo.update(cart)


class RemoveFromCartCommandHandler:
    # """Handler for removing items from the cart"""
    def __init__(self, repo: CartRepository):
        self.repo = repo

    async def handle(self, command: RemoveFromCartCommand) -> Cart:
        cart = await self.repo.get_by_user_id(command.user_id)
        if not cart:
            raise DomainError(f"Cart not found for user {command.user_id}")

        cart.remove_item(command.product_id)
        return await self.repo.update(cart)


class ClearCartCommandHandler:
    # """Handler for clearing the cart"""
    def __init__(self, repo: CartRepository):
        self.repo = repo

    async def handle(self, command: ClearCartCommand) -> Cart:
        cart = await self.repo.get_by_user_id(command.user_id)
        if not cart:
            raise DomainError(f"Cart not found for user {command.user_id}")

        cart.clear()
        return await self.repo.update(cart)
