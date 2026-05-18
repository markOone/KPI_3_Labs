from typing import Callable, Dict, List
from abc import ABC, abstractmethod
from src.domain.events.domain_events import DomainEvent


class EventHandler(ABC):
    """Base class for event handlers"""

    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        pass

    @abstractmethod
    def get_event_type(self) -> str:
        pass


class EventBus(ABC):
    """Abstract event bus interface"""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        pass

    @abstractmethod
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        pass


class InProcessEventBus(EventBus):
    """In-process event bus implementation"""

    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}

    async def publish(self, event: DomainEvent) -> None:
        event_type = event.get_event_type()
        handlers = self._handlers.get(event_type, [])

        for handler in handlers:
            await handler.handle(event)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
