import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

from src.main import app
from src.database.engine import db_helper
from src.config.dependencies import get_current_user
from src.database.models import User, Cart, CartItem, Product, Stock, Order

pytestmark = pytest.mark.asyncio

# Фейковий користувач для авторизації
mock_user = User(id=1, username="test_user", email="test@example.com")

async def override_get_current_user():
    return mock_user

async def test_checkout_empty_cart():
    """Тест: спроба оформити замовлення з порожнім кошиком"""
    mock_session = AsyncMock()
    
    mock_cart_res = MagicMock()
    mock_cart_res.unique.return_value.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_cart_res

    async def override_get_db_session():
        yield mock_session

    app.dependency_overrides[db_helper.get_db_session] = override_get_db_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/orders/checkout")

    assert response.status_code == 400
    assert response.json() == {"detail": "Cart is empty"}
    
    app.dependency_overrides.clear()


async def test_checkout_out_of_stock():
    """Тест: спроба купити більше, ніж є на складі"""
    mock_session = AsyncMock()
    
    mock_cart = Cart(id=1, user_id=1)
    mock_product = Product(id=1, name="Клавіатура", price=1500.0)
    mock_cart_item = CartItem(id=1, cart_id=1, product_id=1, quantity=5)
    mock_cart_item.product = mock_product
    mock_cart.items = [mock_cart_item]

    mock_cart_res = MagicMock()
    mock_cart_res.unique.return_value.scalar_one_or_none.return_value = mock_cart

    mock_stock = Stock(id=1, product_id=1, quantity=2)
    mock_stock_res = MagicMock()
    mock_stock_res.scalars().all.return_value = [mock_stock]

    mock_session.execute.side_effect = [mock_cart_res, mock_stock_res]

    async def override_get_db_session():
        yield mock_session

    app.dependency_overrides[db_helper.get_db_session] = override_get_db_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/orders/checkout")

    assert response.status_code == 409
    assert "is out of stock" in response.json()["detail"]
    
    app.dependency_overrides.clear()


async def test_checkout_success():
    """Тест: успішне оформлення замовлення"""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    
    mock_cart = Cart(id=1, user_id=1)
    mock_product = Product(id=1, name="Клавіатура", price=1500.0)
    mock_cart_item = CartItem(id=1, cart_id=1, product_id=1, quantity=2)
    mock_cart_item.product = mock_product
    mock_cart.items = [mock_cart_item]

    mock_cart_res = MagicMock()
    mock_cart_res.unique.return_value.scalar_one_or_none.return_value = mock_cart

    mock_stock = Stock(id=1, product_id=1, quantity=10)
    mock_stock_res = MagicMock()
    mock_stock_res.scalars().all.return_value = [mock_stock]

    mock_delete_res = MagicMock()

    mock_session.execute.side_effect = [mock_cart_res, mock_stock_res, mock_delete_res]

    async def mock_refresh(instance):
        instance.id = 99
        instance.status = "created" 
        instance.total_price = Decimal("3000.0")

    mock_session.refresh.side_effect = mock_refresh

    async def override_get_db_session():
        yield mock_session

    app.dependency_overrides[db_helper.get_db_session] = override_get_db_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/orders/checkout")

    assert response.status_code == 201
    
    assert float(response.json()["total_price"]) == 3000.0
    assert response.json()["status"] == "created"
    
    assert mock_stock.quantity == 8 
    
    app.dependency_overrides.clear()