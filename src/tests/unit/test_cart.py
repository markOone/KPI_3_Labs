import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock

from src.main import app
from src.database.engine import db_helper
from src.config.dependencies import get_current_user
from src.database.models import User, Product, Stock

pytestmark = pytest.mark.asyncio

mock_user = User(id=1, username="test_user", email="test@example.com")

async def override_get_current_user():
    return mock_user


async def test_get_cart_empty():
    """Тест: отримання порожнього кошика"""
    mock_session = AsyncMock()
    
    mock_result = MagicMock()
    mock_result.unique.return_value.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    async def override_get_db_session():
        yield mock_session

    app.dependency_overrides[db_helper.get_db_session] = override_get_db_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/cart")

    assert response.status_code == 200
    assert response.json() == {"items": []}
    
    app.dependency_overrides.clear()


async def test_add_item_insufficient_stock():
    """Бізнес-логіка: не можна додати товар, якщо його мало на складі"""
    mock_session = AsyncMock()
    
    mock_product = Product(id=1, name="Стілець", price=100.0)
    mock_stock = Stock(product_id=1, quantity=2)
    mock_product.stock = mock_stock
    
    mock_result = MagicMock()
    mock_result.unique.return_value.scalar_one_or_none.return_value = mock_product
    mock_session.execute.return_value = mock_result

    async def override_get_db_session():
        yield mock_session

    app.dependency_overrides[db_helper.get_db_session] = override_get_db_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {"product_id": 1, "quantity": 5}
        response = await ac.post("/cart/items", json=payload)

    assert response.status_code == 400
    assert "Not enough stock" in response.json()["detail"]
    
    app.dependency_overrides.clear()


async def test_add_item_success():
    """Тест: успішне додавання товару в новий кошик"""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    
    mock_product = Product(id=1, name="Стілець", price=100.0)
    mock_product.stock = Stock(product_id=1, quantity=10)
    mock_product_result = MagicMock()
    mock_product_result.unique.return_value.scalar_one_or_none.return_value = mock_product
    
    mock_cart_result = MagicMock()
    mock_cart_result.unique.return_value.scalar_one_or_none.return_value = None # Кошика ще немає
    
    mock_session.execute.side_effect = [mock_product_result, mock_cart_result]
    
    async def mock_refresh(instance):
        instance.id = 1
    mock_session.refresh.side_effect = mock_refresh

    async def override_get_db_session():
        yield mock_session

    app.dependency_overrides[db_helper.get_db_session] = override_get_db_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {"product_id": 1, "quantity": 2}
        response = await ac.post("/cart/items", json=payload)

    assert response.status_code == 201
    assert response.json()["product_id"] == 1
    assert response.json()["quantity"] == 2
    
    app.dependency_overrides.clear()