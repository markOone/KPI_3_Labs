import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_auth_flow(client: AsyncClient):
    reg_res = await client.post("/auth/register", json={
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "supersecretpassword123"
    })
    assert reg_res.status_code == 201

    login_res = await client.post("/auth/login", data={
        "username": "testuser",
        "password": "supersecretpassword123"
    })
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    me_res = await client.get("/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "testuser"