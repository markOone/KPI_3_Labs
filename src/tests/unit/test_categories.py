import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock

from src.main import app
from src.database.engine import db_helper
from src.database.models import Category

pytestmark = pytest.mark.asyncio


async def test_create_category_success():
    """Тест успішного створення категорії"""
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
        response = await ac.post("/categories/", json={"name": "Електроніка"})

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Електроніка"
    assert data["id"] == 1
    
    assert mock_session.add.called
    assert mock_session.commit.called
    
    app.dependency_overrides.clear()


async def test_create_category_conflict():
    """Тест на спробу створити категорію з існуючою назвою"""
    mock_session = AsyncMock()
    
    existing_category = Category(id=1, name="Електроніка")
    mock_check_result = MagicMock()
    mock_check_result.scalar_one_or_none.return_value = existing_category
    mock_session.execute.return_value = mock_check_result

    async def override_get_db_session():
        yield mock_session

    app.dependency_overrides[db_helper.get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/categories/", json={"name": "Електроніка"})

    assert response.status_code == 409
    assert response.json() == {"detail": "Категорія з такою назвою вже існує."}
    
    app.dependency_overrides.clear()


async def test_get_categories():
    """Тест отримання списку категорій"""
    mock_session = AsyncMock()
    
    fake_categories = [
        Category(id=1, name="Смартфони"),
        Category(id=2, name="Ноутбуки")
    ]
    
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = fake_categories
    mock_session.execute.return_value = mock_result

    async def override_get_db_session():
        yield mock_session

    app.dependency_overrides[db_helper.get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/categories/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Смартфони"
    assert data[1]["name"] == "Ноутбуки"
    
    app.dependency_overrides.clear()


async def test_get_category_not_found():
    """Тест отримання неіснуючої категорії за ID"""
    mock_session = AsyncMock()
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    async def override_get_db_session():
        yield mock_session

    app.dependency_overrides[db_helper.get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/categories/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Категорію не знайдено."}
    
    app.dependency_overrides.clear()