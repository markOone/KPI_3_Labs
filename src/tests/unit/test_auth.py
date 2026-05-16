import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock

from src.main import app
from src.database.engine import db_helper
from src.database.models import User
from src.auth.hashing import Hasher

pytestmark = pytest.mark.asyncio

async def test_register_success():
    """Тест: успішна реєстрація нового користувача"""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    async def override_get_db_session():
        yield mock_session

    app.dependency_overrides[db_helper.get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/auth/register", json={
            "username": "new_user",
            "email": "test@example.com",
            "password": "SuperSecretPassword123",
            "group_id": 2
        })

    assert response.status_code == 201
    assert response.json() == {"status": "success"}
    
    app.dependency_overrides.clear()


async def test_register_invalid_email():
    """Тест: спроба реєстрації з неправильним форматом email"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/auth/register", json={
            "username": "bad_user",
            "email": "not-an-email", 
            "password": "password123"
        })

    assert response.status_code == 422


async def test_login_success():
    """Тест: успішний логін та отримання токенів"""
    mock_session = AsyncMock()
    
    test_password = "MySecurePassword"
    hashed_password = Hasher.get_password_hash(test_password)
    
    mock_user = User(id=1, username="test_user", email="test@test.com", password_hash=hashed_password)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result

    async def override_get_db_session():
        yield mock_session

    app.dependency_overrides[db_helper.get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/auth/login", data={
            "username": "test_user",
            "password": test_password 
        })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    
    app.dependency_overrides.clear()

