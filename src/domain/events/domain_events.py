from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Tuple
from abc import ABC, abstractmethod


class DomainEvent(ABC):
    """Base class for all domain events"""

    def __init__(self):
        self.occurred_at = datetime.now(timezone.utc)

    @abstractmethod
    def get_event_type(self) -> str:
        pass


@dataclass(frozen=True)
class OrderCreatedEvent(DomainEvent):
    """Raised when order is successfully created"""

    order_id: int
    user_id: int
    items: List[Tuple[int, int, float]]
    total_price: float

    def get_event_type(self) -> str:
        return "order.created"


@dataclass(frozen=True)
class OrderCancelledEvent(DomainEvent):
    """Raised when order is cancelled"""

    order_id: int
    user_id: int

    def get_event_type(self) -> str:
        return "order.cancelled"


@dataclass(frozen=True)
class OrderConfirmedEvent(DomainEvent):
    """Raised when order is confirmed"""

    order_id: int
    user_id: int

    def get_event_type(self) -> str:
        return "order.confirmed"
