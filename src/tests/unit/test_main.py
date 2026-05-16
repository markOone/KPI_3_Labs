import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock

from src.main import app
from src.database.engine import db_helper

pytestmark = pytest.mark.asyncio

async def test_read_root():
    """Перевірка базового ендпоінту /health"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
        
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


async def test_check_database_health_ok():
    """Перевірка ендпоінту /health/database (успішне підключення)"""
    mock_session = AsyncMock()
    mock_session.execute.return_value = None 

    async def override_get_db_session():
        yield mock_session

    # Підміняємо реальну базу на наш мок
    app.dependency_overrides[db_helper.get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health/database")
        
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "online"}
    
    app.dependency_overrides.clear()


async def test_check_database_health_fail():
    """Перевірка ендпоінту /health/database (помилка бази даних)"""
    mock_session = AsyncMock()
    mock_session.execute.side_effect = Exception("DB Connection Lost")

    async def override_get_db_session():
        yield mock_session

    app.dependency_overrides[db_helper.get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health/database")
        
    assert response.status_code == 500
    assert response.json() == {"detail": "Database is offline or unresponsive"}
    
    app.dependency_overrides.clear()