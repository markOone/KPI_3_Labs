import pytest
from unittest.mock import AsyncMock, ANY
import datetime
from fastapi import HTTPException

from src.application.commands.order_commands import CancelOrderCommand, ProcessCheckoutCommand
from src.application.commands.order_command_handlers import CancelOrderCommandHandler, ProcessCheckoutCommandHandler
from src.domain.entities.entities import Order, OrderItem, Cart, CartItem, Product
from src.domain.value_objects.value_objects import Quantity, Money, Sku
from src.domain.errors.domain_errors import OrderNotFoundError, InvalidOrderStatusError

# ==========================================
# ДОПОМІЖНІ ФУНКЦІЇ ДЛЯ ТЕСТІВ
# ==========================================
def create_fake_order(status: str = "pending") -> Order:
    return Order(
        id=1,
        user_id=10,
        items=[OrderItem(id=1, product_id=100, quantity=Quantity(2), price_at_purchase=Money(500.0))],
        status=status,
        total_price=Money(1000.0),
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )

def create_fake_cart() -> Cart:
    return Cart(
        id=1,
        user_id=10,
        items=[CartItem(id=1, product_id=100, quantity=Quantity(2))]
    )

def create_fake_product() -> Product:
    return Product(
        id=100,
        name="Keyboard",
        sku=Sku("KB-01"),
        price=Money(500.0),
        category_id=1
    )

# ==========================================
# ТЕСТИ ДЛЯ СКАСУВАННЯ ЗАМОВЛЕННЯ (Cancel Order)
# ==========================================
@pytest.mark.asyncio
async def test_cancel_order_success():
    """Перевіряє, що замовлення в статусі 'pending' успішно скасовується."""
    # Arrange
    mock_repo = AsyncMock()
    order = create_fake_order(status="pending")
    mock_repo.get_by_id.return_value = order
    
    handler = CancelOrderCommandHandler(mock_repo)
    command = CancelOrderCommand(order_id=1)

    # Act
    await handler.handle(command)

    # Assert
    assert order.status == "cancelled"
    mock_repo.update.assert_called_once_with(order)

@pytest.mark.asyncio
async def test_cancel_order_throws_if_not_found():
    """Перевіряє помилку, якщо замовлення не існує."""
    # Arrange
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None
    
    handler = CancelOrderCommandHandler(mock_repo)
    command = CancelOrderCommand(order_id=999)

    # Act & Assert
    with pytest.raises(OrderNotFoundError, match="Order 999 not found"):
        await handler.handle(command)

@pytest.mark.asyncio
async def test_cancel_order_throws_if_invalid_status():
    """Перевіряє інваріант: не можна скасувати відправлене ('shipped') замовлення."""
    # Arrange
    mock_repo = AsyncMock()
    order = create_fake_order(status="shipped") # Вже відправлено!
    mock_repo.get_by_id.return_value = order
    
    handler = CancelOrderCommandHandler(mock_repo)
    command = CancelOrderCommand(order_id=1)

    # Act & Assert
    with pytest.raises(InvalidOrderStatusError, match="Cannot cancel order with status 'shipped'"):
        await handler.handle(command)
    
    # Переконуємось, що ми не спробували зберегти хибний стан
    mock_repo.update.assert_not_called()


# ==========================================
# ТЕСТИ ДЛЯ ОФОРМЛЕННЯ ЗАМОВЛЕННЯ (Checkout)
# ==========================================
@pytest.mark.asyncio
async def test_checkout_throws_if_cart_empty():
    """Перевіряє, що оформлення зупиняється, якщо кошик порожній або відсутній."""
    # Arrange
    cart_repo = AsyncMock()
    product_repo = AsyncMock()
    order_repo = AsyncMock()
    
    cart_repo.get_by_user_id.return_value = None # Кошик не знайдено
    
    handler = ProcessCheckoutCommandHandler(cart_repo, product_repo, order_repo)
    command = ProcessCheckoutCommand(user_id=10)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await handler.handle(command)
        
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Cart is empty"

@pytest.mark.asyncio
async def test_checkout_success_creates_order_and_clears_cart():
    """
    Перевіряє Happy Path: 
    1. Беремо товари з кошика.
    2. Дістаємо ціни з ProductRepository.
    3. Створюємо Order з правильною сумою.
    4. Видаляємо кошик.
    """
    # Arrange
    cart_repo = AsyncMock()
    product_repo = AsyncMock()
    order_repo = AsyncMock()
    
    # Налаштовуємо моки
    cart = create_fake_cart()
    product = create_fake_product() # Ціна 500.0
    expected_order = create_fake_order() # Імітуємо створене замовлення з ID=1
    
    cart_repo.get_by_user_id.return_value = cart
    product_repo.get_by_id.return_value = product
    order_repo.create.return_value = expected_order
    
    handler = ProcessCheckoutCommandHandler(cart_repo, product_repo, order_repo)
    command = ProcessCheckoutCommand(user_id=10)

    # Act
    result_id = await handler.handle(command)

    # Assert 1: Перевіряємо, що повернувся правильний ID
    assert result_id == expected_order.id
    
    # Assert 2: Перевіряємо, що кошик був видалений
    cart_repo.delete.assert_called_once_with(cart.id)
    
    # Assert 3: Перевіряємо, що замовлення створено з правильними даними
    order_repo.create.assert_called_once()
    created_order_arg = order_repo.create.call_args[0][0] # Дістаємо об'єкт Order, який передали в create()
    
    assert created_order_arg.user_id == 10
    assert created_order_arg.status == "pending"
    # Кількість 2 * Ціна 500.0 = 1000.0
    assert created_order_arg.total_price.amount == 1000.0 
    assert len(created_order_arg.items) == 1
    assert created_order_arg.items[0].product_id == 100