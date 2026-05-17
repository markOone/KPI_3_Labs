import pytest
from unittest.mock import AsyncMock

from src.application.commands.product_commands import (
    CreateProductCommand,
    UpdateProductCommand,
    DeleteProductCommand
)
from src.application.commands.product_command_handlers import (
    CreateProductCommandHandler,
    UpdateProductCommandHandler,
    DeleteProductCommandHandler
)
from src.domain.entities.entities import Product
from src.domain.value_objects.value_objects import Sku, Money
from src.domain.errors.domain_errors import ProductNotFoundError, DuplicateSkuError

# ==========================================
# ДОПОМІЖНІ ФУНКЦІЇ ДЛЯ ТЕСТІВ
# ==========================================
def create_fake_product(product_id: int = 1, sku_val: str = "TEST-123") -> Product:
    """Створює валідну сутність продукту для використання у моках."""
    return Product(
        id=product_id,
        name="Test Product",
        sku=Sku(sku_val),
        price=Money(100.0),
        category_id=1
    )

# ==========================================
# ТЕСТИ ДЛЯ СТВОРЕННЯ (Create)
# ==========================================
@pytest.mark.asyncio
async def test_create_product_success():
    """Перевіряє успішне створення продукту."""
    # Arrange
    mock_repo = AsyncMock()
    # Імітуємо, що такого SKU ще немає в базі (для Factory)
    mock_repo.get_by_sku.return_value = None
    # Імітуємо повернення збереженого продукту з БД
    expected_product = create_fake_product()
    mock_repo.create.return_value = expected_product
    
    handler = CreateProductCommandHandler(mock_repo)
    command = CreateProductCommand(name="New Mouse", sku="MOUSE-001", price=50.0, category_id=1)

    # Act
    result_id = await handler.handle(command)

    # Assert
    assert result_id == expected_product.id
    mock_repo.create.assert_called_once()

# ==========================================
# ТЕСТИ ДЛЯ ОНОВЛЕННЯ (Update)
# ==========================================
@pytest.mark.asyncio
async def test_update_product_throws_not_found_error():
    """Перевіряє, що генерується помилка, якщо продукт не знайдено."""
    # Arrange
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None # Продукту немає
    
    handler = UpdateProductCommandHandler(mock_repo)
    command = UpdateProductCommand(product_id=999, name="New Name")

    # Act & Assert
    with pytest.raises(ProductNotFoundError, match="Product with ID 999 not found"):
        await handler.handle(command)
        
    mock_repo.update.assert_not_called()

@pytest.mark.asyncio
async def test_update_product_throws_duplicate_sku_error():
    """Перевіряє, що не можна встановити SKU, який вже належить іншому продукту."""
    # Arrange
    mock_repo = AsyncMock()
    # Продукт, який ми оновлюємо
    existing_product = create_fake_product(product_id=1, sku_val="OLD-SKU")
    # Інший продукт у базі, який вже має бажаний SKU
    conflict_product = create_fake_product(product_id=2, sku_val="NEW-SKU")
    
    mock_repo.get_by_id.return_value = existing_product
    mock_repo.get_by_sku.return_value = conflict_product
    
    handler = UpdateProductCommandHandler(mock_repo)
    command = UpdateProductCommand(product_id=1, sku="NEW-SKU")

    # Act & Assert
    with pytest.raises(DuplicateSkuError, match="Product with SKU 'NEW-SKU' already exists"):
        await handler.handle(command)

@pytest.mark.asyncio
async def test_update_product_success():
    """Перевіряє успішне оновлення полів продукту."""
    # Arrange
    mock_repo = AsyncMock()
    existing_product = create_fake_product()
    mock_repo.get_by_id.return_value = existing_product
    
    handler = UpdateProductCommandHandler(mock_repo)
    command = UpdateProductCommand(product_id=1, name="Updated Name", price=999.99)

    # Act
    await handler.handle(command)

    # Assert
    assert existing_product.name == "Updated Name"
    assert existing_product.price.amount == 999.99
    mock_repo.update.assert_called_once_with(existing_product)

# ==========================================
# ТЕСТИ ДЛЯ ВИДАЛЕННЯ (Delete)
# ==========================================
@pytest.mark.asyncio
async def test_delete_product_success():
    """Перевіряє успішне видалення продукту."""
    # Arrange
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = create_fake_product()
    
    handler = DeleteProductCommandHandler(mock_repo)
    command = DeleteProductCommand(product_id=1)

    # Act
    await handler.handle(command)

    # Assert
    mock_repo.delete.assert_called_once_with(1)