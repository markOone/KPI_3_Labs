import datetime
from src.application.commands.order_commands import ProcessCheckoutCommand, CreateOrderCommand, CancelOrderCommand
from src.domain.entities.entities import Order, OrderItem
from src.domain.value_objects.value_objects import Quantity, Money
from src.domain.repositories.repositories import CartRepository, OrderRepository, ProductRepository
from src.domain.errors.domain_errors import InvalidOrderStatusError, OrderNotFoundError
from fastapi import HTTPException

class ProcessCheckoutCommandHandler:
    def __init__(self, cart_repository: CartRepository, product_repository: ProductRepository, order_repository: OrderRepository):
        self.cart_repository = cart_repository
        self.product_repository = product_repository
        self.order_repository = order_repository

    async def handle(self, command: ProcessCheckoutCommand) -> int:
        cart = await self.cart_repository.get_by_user_id(command.user_id)
        if not cart or not cart.items:
            raise HTTPException(status_code=400, detail="Cart is empty")

        items_data = []
        for item in cart.items:
            product = await self.product_repository.get_by_id(item.product_id)
            if not product:
                raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
            items_data.append((item.product_id, item.quantity.value, product.price.amount))

        order_items = []
        for index, item in enumerate(items_data):
            product_id, quantity, price = item
            order_items.append(
                OrderItem(
                    id=index,
                    product_id=product_id,
                    quantity=Quantity(quantity),
                    price_at_purchase=Money(price),
                )
            )

        total_price = sum(price * qty for _, qty, price in items_data)
        order = Order(
            id=0,
            user_id=command.user_id,
            items=order_items,
            status="pending",
            total_price=Money(total_price),
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )

        order.validate()

        created_order = await self.order_repository.create(order)
        await self.cart_repository.delete(cart.id)
        return created_order.id


class CreateOrderCommandHandler:
    def __init__(self, order_repository: OrderRepository, cart_repository: CartRepository):
        self.order_repository = order_repository
        self.cart_repository = cart_repository

    async def handle(self, command: CreateOrderCommand) -> int:
        order_items = []

        for index, item in enumerate(command.items):
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
            user_id=command.user_id,
            items=order_items,
            status="pending",
            total_price=Money(command.total_price),
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )

        order.validate()

        created_order = await self.order_repository.create(order)
        await self.cart_repository.delete(command.cart_id)
        return created_order.id


class CancelOrderCommandHandler:
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    async def handle(self, command: CancelOrderCommand) -> None:
        order = await self.order_repository.get_by_id(command.order_id)
        if not order:
            raise OrderNotFoundError(f"Order {command.order_id} not found")

        if not order.can_cancel():
            raise InvalidOrderStatusError(
                f"Cannot cancel order with status '{order.status}'"
            )

        order.status = "cancelled"
        await self.order_repository.update(order)