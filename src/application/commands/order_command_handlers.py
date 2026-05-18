import datetime
import logging
from src.application.services.notification_event_handlers import NotificationEventHandler
from src.application.commands.order_commands import ProcessCheckoutCommand, CreateOrderCommand, CancelOrderCommand
from src.domain.entities.entities import Order, OrderItem
from src.domain.value_objects.value_objects import Quantity, Money
from src.domain.repositories.repositories import CartRepository, OrderRepository, ProductRepository, UserRepository
from src.domain.errors.domain_errors import InvalidOrderStatusError, OrderNotFoundError
from src.application.services.notifications import NotificationService
from src.infrastructure.event_bus import EventBus
from src.domain.events.domain_events import OrderCreatedEvent, OrderCancelledEvent
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class ProcessCheckoutCommandHandler:
    def __init__(
        self,
        cart_repository: CartRepository,
        product_repository: ProductRepository,
        order_repository: OrderRepository,
        user_repository: UserRepository,
        notification_service: NotificationService,
        event_bus: EventBus,
        stock_repository=None,
        use_async: bool = True,
    ):
        self.cart_repository = cart_repository
        self.product_repository = product_repository
        self.order_repository = order_repository
        self.user_repository = user_repository
        self.notification_service = notification_service
        self.event_bus = event_bus
        self.stock_repository = stock_repository
        self.use_async = use_async

        if self.use_async:
            order_created_handler = NotificationEventHandler(
                user_repository=self.user_repository,
                order_repository=self.order_repository,
                event_type="order.created"
            )
            self.event_bus.subscribe("order.created", order_created_handler)

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

        if self.stock_repository:
            for item in items_data:
                product_id, quantity, _ = item
                stock = await self.stock_repository.get_by_product_id(product_id)
                if stock:
                    stock.reduce(Quantity(quantity))
                    await self.stock_repository.update(stock)

        await self.cart_repository.delete(cart.id)

        user = await self.user_repository.get_by_id(command.user_id)
        if user:
            if self.use_async:
                event = OrderCreatedEvent(
                    order_id=created_order.id,
                    user_id=command.user_id,
                    items=items_data,
                    total_price=total_price,
                )
                await self.event_bus.publish(event)
            else:
                try:
                    await self.notification_service.send_order_created(created_order, user)
                except Exception as e:
                    logger.error(f"Failed to send synchronous notification for order {created_order.id}: {e}")

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
    def __init__(
        self,
        order_repository: OrderRepository,
        user_repository: UserRepository,
        notification_service: NotificationService,
        event_bus: EventBus,
        use_async: bool = False,
    ):
        self.order_repository = order_repository
        self.user_repository = user_repository
        self.notification_service = notification_service
        self.event_bus = event_bus
        self.use_async = use_async

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

        user = await self.user_repository.get_by_id(order.user_id)
        if user:
            if self.use_async:
                event = OrderCancelledEvent(
                    order_id=order.id,
                    user_id=order.user_id,
                )
                await self.event_bus.publish(event)
            else:
                try:
                    await self.notification_service.send_order_cancelled(order, user)
                except Exception as e:
                    logger.error(f"Failed to send synchronous notification for cancelled order {order.id}: {e}")