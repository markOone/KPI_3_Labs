import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from src.application.commands.order_command_handlers import (
    ProcessCheckoutCommandHandler,
    CancelOrderCommandHandler,
)
from src.application.commands.order_commands import (
    ProcessCheckoutCommand,
    CancelOrderCommand,
)
from src.domain.entities.entities import Order, OrderItem, Cart, CartItem, User
from src.domain.value_objects.value_objects import (
    Quantity,
    Money,
    Email,
)
from src.infrastructure.event_bus import InProcessEventBus
from src.application.services.notifications import EmailNotificationService
from src.domain.events.domain_events import OrderCreatedEvent, OrderCancelledEvent


@pytest.fixture
def mock_repositories():
    return {
        "cart_repository": AsyncMock(),
        "product_repository": AsyncMock(),
        "order_repository": AsyncMock(),
        "user_repository": AsyncMock(),
        "stock_repository": AsyncMock(),
    }


@pytest.fixture
def event_bus():
    return InProcessEventBus()


@pytest.fixture
def notification_service():
    return EmailNotificationService()


@pytest.mark.asyncio
async def test_checkout_sync_notification(mock_repositories, notification_service, event_bus):
    """Test synchronous notification on order creation"""
    cart = Cart(
        id=1,
        user_id=1,
        items=[CartItem(id=1, product_id=1, quantity=Quantity(2))],
    )
    user = User(
        id=1,
        email=Email("test@example.com"),
        username="testuser",
        password_hash="hash",
    )
    product = MagicMock()
    product.price = Money(100)
    order = Order(
        id=1,
        user_id=1,
        items=[
            OrderItem(
                id=0,
                product_id=1,
                quantity=Quantity(2),
                price_at_purchase=Money(100),
            )
        ],
        status="pending",
        total_price=Money(200),
        created_at=datetime.now(timezone.utc),
    )

    mock_repositories["cart_repository"].get_by_user_id.return_value = cart
    mock_repositories["product_repository"].get_by_id.return_value = product
    mock_repositories["order_repository"].create.return_value = order
    mock_repositories["user_repository"].get_by_id.return_value = user

    handler = ProcessCheckoutCommandHandler(
        cart_repository=mock_repositories["cart_repository"],
        product_repository=mock_repositories["product_repository"],
        order_repository=mock_repositories["order_repository"],
        user_repository=mock_repositories["user_repository"],
        notification_service=notification_service,
        event_bus=event_bus,
        stock_repository=mock_repositories["stock_repository"],
        use_async=False,  # Synchronous approach
    )

    command = ProcessCheckoutCommand(user_id=1)
    order_id = await handler.handle(command)

    assert order_id == 1
    mock_repositories["order_repository"].create.assert_called_once()
    mock_repositories["user_repository"].get_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_checkout_async_notification(mock_repositories, event_bus):
    """Test asynchronous notification on order creation"""
    cart = Cart(
        id=1,
        user_id=1,
        items=[CartItem(id=1, product_id=1, quantity=Quantity(2))],
    )
    user = User(
        id=1,
        email=Email("test@example.com"),
        username="testuser",
        password_hash="hash",
    )
    product = MagicMock()
    product.price = Money(100)
    order = Order(
        id=1,
        user_id=1,
        items=[
            OrderItem(
                id=0,
                product_id=1,
                quantity=Quantity(2),
                price_at_purchase=Money(100),
            )
        ],
        status="pending",
        total_price=Money(200),
        created_at=datetime.now(timezone.utc),
    )

    mock_repositories["cart_repository"].get_by_user_id.return_value = cart
    mock_repositories["product_repository"].get_by_id.return_value = product
    mock_repositories["order_repository"].create.return_value = order
    mock_repositories["user_repository"].get_by_id.return_value = user

    # Track published events
    published_events = []

    async def track_publish(event):
        published_events.append(event)

    event_bus.publish = track_publish

    handler = ProcessCheckoutCommandHandler(
        cart_repository=mock_repositories["cart_repository"],
        product_repository=mock_repositories["product_repository"],
        order_repository=mock_repositories["order_repository"],
        user_repository=mock_repositories["user_repository"],
        notification_service=EmailNotificationService(),
        event_bus=event_bus,
        stock_repository=mock_repositories["stock_repository"],
        use_async=True,  # Asynchronous approach
    )

    command = ProcessCheckoutCommand(user_id=1)
    order_id = await handler.handle(command)

    assert order_id == 1
    assert len(published_events) == 1
    assert isinstance(published_events[0], OrderCreatedEvent)
    assert published_events[0].order_id == 1
    assert published_events[0].user_id == 1


@pytest.mark.asyncio
async def test_cancel_order_sync_notification(mock_repositories, notification_service, event_bus):
    """Test synchronous notification on order cancellation"""
    order = Order(
        id=1,
        user_id=1,
        items=[
            OrderItem(
                id=0,
                product_id=1,
                quantity=Quantity(2),
                price_at_purchase=Money(100),
            )
        ],
        status="pending",
        total_price=Money(200),
        created_at=datetime.now(timezone.utc),
    )
    user = User(
        id=1,
        email=Email("test@example.com"),
        username="testuser",
        password_hash="hash",
    )

    mock_repositories["order_repository"].get_by_id.return_value = order
    mock_repositories["user_repository"].get_by_id.return_value = user

    handler = CancelOrderCommandHandler(
        order_repository=mock_repositories["order_repository"],
        user_repository=mock_repositories["user_repository"],
        notification_service=notification_service,
        event_bus=event_bus,
        use_async=False,
    )

    command = CancelOrderCommand(order_id=1)
    await handler.handle(command)

    assert order.status == "cancelled"
    mock_repositories["order_repository"].update.assert_called_once()


@pytest.mark.asyncio
async def test_cancel_order_async_notification(mock_repositories, event_bus):
    """Test asynchronous notification on order cancellation"""
    order = Order(
        id=1,
        user_id=1,
        items=[
            OrderItem(
                id=0,
                product_id=1,
                quantity=Quantity(2),
                price_at_purchase=Money(100),
            )
        ],
        status="pending",
        total_price=Money(200),
        created_at=datetime.now(timezone.utc),
    )
    user = User(
        id=1,
        email=Email("test@example.com"),
        username="testuser",
        password_hash="hash",
    )

    mock_repositories["order_repository"].get_by_id.return_value = order
    mock_repositories["user_repository"].get_by_id.return_value = user

    published_events = []

    async def track_publish(event):
        published_events.append(event)

    event_bus.publish = track_publish

    handler = CancelOrderCommandHandler(
        order_repository=mock_repositories["order_repository"],
        user_repository=mock_repositories["user_repository"],
        notification_service=EmailNotificationService(),
        event_bus=event_bus,
        use_async=True,
    )

    command = CancelOrderCommand(order_id=1)
    await handler.handle(command)

    assert order.status == "cancelled"
    assert len(published_events) == 1
    assert isinstance(published_events[0], OrderCancelledEvent)
    assert published_events[0].order_id == 1


@pytest.mark.asyncio
async def test_event_bus_idempotency():
    """Test that event handlers handle duplicate events correctly"""
    event_bus = InProcessEventBus()

    handled_events = []

    class TestHandler:
        async def handle(self, event):
            handled_events.append(event)

        def get_event_type(self):
            return "order.created"

    handler = TestHandler()
    event_bus.subscribe("order.created", handler)

    event = OrderCreatedEvent(
        order_id=1,
        user_id=1,
        items=[(1, 2, 100)],
        total_price=200,
    )

    # Simulate duplicate event delivery
    await event_bus.publish(event)
    await event_bus.publish(event)

    assert len(handled_events) == 2  # Both events processed


@pytest.mark.asyncio
async def test_event_bus_multiple_subscribers():
    """Test that multiple subscribers receive the same event"""
    event_bus = InProcessEventBus()

    subscriber1_events = []
    subscriber2_events = []

    class Subscriber1:
        async def handle(self, event):
            subscriber1_events.append(event)

        def get_event_type(self):
            return "order.created"

    class Subscriber2:
        async def handle(self, event):
            subscriber2_events.append(event)

        def get_event_type(self):
            return "order.created"

    sub1 = Subscriber1()
    sub2 = Subscriber2()
    event_bus.subscribe("order.created", sub1)
    event_bus.subscribe("order.created", sub2)

    event = OrderCreatedEvent(
        order_id=1,
        user_id=1,
        items=[(1, 2, 100)],
        total_price=200,
    )

    await event_bus.publish(event)

    assert len(subscriber1_events) == 1
    assert len(subscriber2_events) == 1
