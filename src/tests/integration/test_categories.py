import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_and_get_categories(client: AsyncClient):
    cat_data_1 = {"name": "Смартфони"}
    response_1 = await client.post("/categories/", json=cat_data_1)
    assert response_1.status_code in (200, 201)
    
    cat_data_2 = {"name": "Планшети"}
    response_2 = await client.post("/categories/", json=cat_data_2)
    assert response_2.status_code in (200, 201)

    response_get = await client.get("/categories/")
    assert response_get.status_code == 200
    
    categories = response_get.json()
    assert len(categories) >= 2
    
    names = [cat["name"] for cat in categories]
    assert "Смартфони" in names
    assert "Планшети" in names