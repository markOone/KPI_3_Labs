import pytest
from unittest.mock import AsyncMock

from src.application.commands.cart_commands import (
    AddToCartCommand,
    RemoveFromCartCommand,
    ClearCartCommand
)
from src.application.commands.cart_handlers import (
    AddToCartCommandHandler,
    RemoveFromCartCommandHandler,
    ClearCartCommandHandler
)
from src.domain.entities.entities import Cart, CartItem
from src.domain.value_objects.value_objects import Quantity
from src.domain.errors.domain_errors import DomainError

# ==========================================
# ДОПОМІЖНІ ФУНКЦІЇ ДЛЯ ТЕСТІВ
# ==========================================
def create_fake_cart(user_id: int = 1) -> Cart:
    return Cart(
        id=1,
        user_id=user_id,
        items=[CartItem(id=1, product_id=100, quantity=Quantity(2))]
    )

# ==========================================
# ТЕСТИ ДЛЯ ADD TO CART
# ==========================================
@pytest.mark.asyncio
async def test_add_to_cart_creates_new_cart_if_not_exists():
    """Перевіряє, що якщо кошика немає, створюється новий, а потім до нього додається товар."""
    # Arrange
    mock_repo = AsyncMock()
    mock_repo.get_by_user_id.return_value = None
    
    # Імітуємо update, повертаючи той самий кошик, який передали
    mock_repo.update.side_effect = lambda cart: cart 
    
    handler = AddToCartCommandHandler(mock_repo)
    command = AddToCartCommand(user_id=10, product_id=50, quantity=3)

    # Act
    updated_cart = await handler.handle(command)

    # Assert
    mock_repo.create.assert_called_once()
    assert updated_cart.user_id == 10
    assert len(updated_cart.items) == 1
    assert updated_cart.items[0].product_id == 50
    assert updated_cart.items[0].quantity.value == 3
    mock_repo.update.assert_called_once_with(updated_cart)

@pytest.mark.asyncio
async def test_add_to_cart_uses_existing_cart():
    """Перевіряє, що якщо кошик є, товар просто додається до нього."""
    # Arrange
    mock_repo = AsyncMock()
    existing_cart = create_fake_cart(user_id=10)
    mock_repo.get_by_user_id.return_value = existing_cart
    mock_repo.update.side_effect = lambda cart: cart
    
    handler = AddToCartCommandHandler(mock_repo)
    command = AddToCartCommand(user_id=10, product_id=999, quantity=1)

    # Act
    updated_cart = await handler.handle(command)

    # Assert
    mock_repo.create.assert_not_called() # Новий кошик не створювався
    assert len(updated_cart.items) == 2 # Був 1 товар, стало 2
    mock_repo.update.assert_called_once_with(existing_cart)

# ==========================================
# ТЕСТИ ДЛЯ REMOVE FROM CART
# ==========================================
@pytest.mark.asyncio
async def test_remove_from_cart_success():
    """Успішне видалення товару з існуючого кошика."""
    # Arrange
    mock_repo = AsyncMock()
    existing_cart = create_fake_cart(user_id=1)
    mock_repo.get_by_user_id.return_value = existing_cart
    mock_repo.update.side_effect = lambda cart: cart
    
    handler = RemoveFromCartCommandHandler(mock_repo)
    command = RemoveFromCartCommand(user_id=1, product_id=100)

    # Act
    updated_cart = await handler.handle(command)

    # Assert
    assert len(updated_cart.items) == 0 # Товар було видалено
    mock_repo.update.assert_called_once_with(existing_cart)

@pytest.mark.asyncio
async def test_remove_from_cart_throws_if_not_found():
    """Помилка, якщо кошик для користувача не знайдено."""
    # Arrange
    mock_repo = AsyncMock()
    mock_repo.get_by_user_id.return_value = None
    
    handler = RemoveFromCartCommandHandler(mock_repo)
    command = RemoveFromCartCommand(user_id=1, product_id=100)

    # Act & Assert
    with pytest.raises(DomainError, match="Cart not found for user 1"):
        await handler.handle(command)

# ==========================================
# ТЕСТИ ДЛЯ CLEAR CART
# ==========================================
@pytest.mark.asyncio
async def test_clear_cart_success():
    """Успішне повне очищення кошика."""
    # Arrange
    mock_repo = AsyncMock()
    existing_cart = create_fake_cart(user_id=5)
    mock_repo.get_by_user_id.return_value = existing_cart
    mock_repo.update.side_effect = lambda cart: cart
    
    handler = ClearCartCommandHandler(mock_repo)
    command = ClearCartCommand(user_id=5)

    # Act
    updated_cart = await handler.handle(command)

    # Assert
    assert len(updated_cart.items) == 0
    mock_repo.update.assert_called_once_with(existing_cart)

@pytest.mark.asyncio
async def test_clear_cart_throws_if_not_found():
    """Помилка очищення: кошик не знайдено."""
    # Arrange
    mock_repo = AsyncMock()
    mock_repo.get_by_user_id.return_value = None
    
    handler = ClearCartCommandHandler(mock_repo)
    command = ClearCartCommand(user_id=5)

    # Act & Assert
    with pytest.raises(DomainError, match="Cart not found for user 5"):
        await handler.handle(command)