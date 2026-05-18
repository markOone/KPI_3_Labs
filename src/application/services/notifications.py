from abc import ABC, abstractmethod
from src.domain.entities.entities import Order, User


class NotificationService(ABC):
    """Abstract notification service interface"""

    @abstractmethod
    async def send_order_created(self, order: Order, user: User) -> None:
        """Send order created notification"""
        pass

    @abstractmethod
    async def send_order_cancelled(self, order: Order, user: User) -> None:
        """Send order cancelled notification"""
        pass


class EmailNotificationService(NotificationService):
    """Email notification service implementation (synchronous)"""

    async def send_order_created(self, order: Order, user: User) -> None:
        print(f"[SYNC] Email sent to {user.email.value}: Order #{order.id} created", flush=True)

    async def send_order_cancelled(self, order: Order, user: User) -> None:
        print(f"[SYNC] Email sent to {user.email.value}: Order #{order.id} cancelled", flush=True)
