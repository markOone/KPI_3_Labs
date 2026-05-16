import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock

from src.main import app
from src.database.engine import db_helper
from src.database.models import Product

pytestmark = pytest.mark.asyncio

async def test_create_product_success():
    """Тест успішного створення товару"""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()  
    
    mock_check_result = MagicMock()
    mock_check_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_check_result

    async def mock_refresh(instance):
        instance.id = 1

    mock_session.refresh.side_effect = mock_refresh

    async def override_get_db_session():
        yield mock_session

    app.dependency_overrides[db_helper.get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        product_data = {
            "name": "Ноутбук",
            "price": 25000.50,
            "sku": "LAP-001",
            "category_id": 1
        }
        response = await ac.post("/products/", json=product_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Ноутбук"
    assert data["sku"] == "LAP-001"
    assert data["id"] == 1
    
    app.dependency_overrides.clear()


async def test_create_product_conflict():
    """Тест на спробу створити товар з існуючим SKU"""
    mock_session = AsyncMock()
    
    existing_product = Product(id=1, name="Старий Ноутбук", sku="LAP-001", price=100.0, category_id=1)
    mock_check_result = MagicMock()
    mock_check_result.scalar_one_or_none.return_value = existing_product
    mock_session.execute.return_value = mock_check_result

    async def override_get_db_session():
        yield mock_session

    app.dependency_overrides[db_helper.get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        product_data = {
            "name": "Новий Ноутбук",
            "price": 30000.00,
            "sku": "LAP-001", 
            "category_id": 1
        }
        response = await ac.post("/products/", json=product_data)

    assert response.status_code == 409
    assert response.json() == {"detail": "Товар з таким артикулом (SKU) вже існує."}
    
    app.dependency_overrides.clear()


async def test_get_products():
    """Тест отримання списку товарів"""
    mock_session = AsyncMock()
    
    fake_products = [
        Product(id=1, name="Ноутбук", price=25000.0, sku="LAP-01", category_id=1),
        Product(id=2, name="Мишка", price=500.0, sku="MS-01", category_id=1)
    ]
    
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = fake_products
    mock_session.execute.return_value = mock_result

    async def override_get_db_session():
        yield mock_session

    app.dependency_overrides[db_helper.get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/products/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Ноутбук"
    
    app.dependency_overrides.clear()


async def test_delete_product_not_found():
    """Тест видалення неіснуючого товару"""
    mock_session = AsyncMock()
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    async def override_get_db_session():
        yield mock_session

    app.dependency_overrides[db_helper.get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.delete("/products/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Товар не знайдено."}
    
    app.dependency_overrides.clear()