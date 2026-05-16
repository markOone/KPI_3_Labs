import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_auth_flow(client: AsyncClient):
    user_data = {
        "username": "test_buyer",
        "email": "buyer@example.com",
        "password": "secure_password_123"
    }
    
    register_response = await client.post("/auth/register", json=user_data)
    assert register_response.status_code in (200, 201), f"Реєстрація провалилася: {register_response.text}"
    
    assert register_response.json() == {"status": "success"}

    login_data = {
        "username": "test_buyer",
        "password": "secure_password_123"
    }
    
    login_response = await client.post("/auth/login", data=login_data)
    assert login_response.status_code == 200, f"Логін провалився: {login_response.text}"
    
    tokens = login_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"