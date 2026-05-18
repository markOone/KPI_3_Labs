from src.infrastructure.event_bus import EventHandler
from src.domain.events.domain_events import OrderCreatedEvent, OrderCancelledEvent, DomainEvent
from src.domain.repositories.repositories import UserRepository, OrderRepository


class NotificationEventHandler(EventHandler):
    """Async notification event handler"""

    def __init__(self, user_repository: UserRepository, order_repository: OrderRepository, event_type: str):
        self.user_repository = user_repository
        self.order_repository = order_repository
        self._event_type = event_type

    async def handle(self, event: DomainEvent) -> None:
        if isinstance(event, OrderCreatedEvent):
            await self._handle_order_created(event)
        elif isinstance(event, OrderCancelledEvent):
            await self._handle_order_cancelled(event)

    def get_event_type(self) -> str:
        return self._event_type

    async def _handle_order_created(self, event: OrderCreatedEvent) -> None:
        order = await self.order_repository.get_by_id(event.order_id)
        user = await self.user_repository.get_by_id(event.user_id)

        if order and user:
            print(f"[ASYNC] Email sent to {user.email.value}: Order #{event.order_id} created", flush=True)

    async def _handle_order_cancelled(self, event: OrderCancelledEvent) -> None:
        order = await self.order_repository.get_by_id(event.order_id)
        user = await self.user_repository.get_by_id(event.user_id)

        if order and user:
            print(f"[ASYNC] Email sent to {user.email.value}: Order #{event.order_id} cancelled", flush=True)
