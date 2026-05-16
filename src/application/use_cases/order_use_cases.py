from typing import List
import datetime
from src.domain.entities.entities import Order, OrderItem
from src.domain.value_objects.value_objects import Quantity, Money
from src.domain.repositories.repositories import CartRepository, OrderRepository
from src.domain.errors.domain_errors import (
    InvalidOrderStatusError,
    OrderNotFoundError,
)


class CreateOrderUseCase:
    """Use case for creating an order from cart"""

    def __init__(
        self, order_repository: OrderRepository, cart_repository: CartRepository
    ):
        self.order_repository = order_repository
        self.cart_repository = cart_repository

    async def execute(
        self, user_id: int, items: list, total_price: float, cart_id: int
    ) -> Order:
        """Create a new order"""
        order_items = []

        for index, item in enumerate(items):
            product_id, quantity, price = item
            order_items.append(
                OrderItem(
                    id=index,
                    product_id=product_id,
                    quantity=Quantity(quantity),
                    price_at_purchase=Money(price),
                )
            )

        order = Order(
            id=0,
            user_id=user_id,
            items=order_items,
            status="pending",
            total_price=Money(total_price),
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )

        order.validate()

        created_order = await self.order_repository.create(order)
        await self.cart_repository.delete(cart_id)
        return created_order


class GetOrderUseCase:
    """Use case for getting an order"""

    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    async def execute(self, order_id: int) -> Order:
        """Get order by ID"""
        order = await self.order_repository.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError(f"Order {order_id} not found")
        return order


class GetUserOrdersUseCase:
    """Use case for getting user's orders"""

    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    async def execute(self, user_id: int) -> List[Order]:
        """Get all orders for user"""
        return await self.order_repository.get_by_user_id(user_id)


class CancelOrderUseCase:
    """Use case for cancelling an order"""

    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    async def execute(self, order_id: int) -> Order:
        """Cancel an order if possible"""
        order = await self.order_repository.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError(f"Order {order_id} not found")

        if not order.can_cancel():
            raise InvalidOrderStatusError(
                f"Cannot cancel order with status '{order.status}'"
            )

        order.status = "cancelled"
        return await self.order_repository.update(order)
