import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_product_integration(client: AsyncClient):
    category_data = {"name": "Електроніка"}
    cat_response = await client.post("/categories/", json=category_data)
    
    assert cat_response.status_code in (200, 201)
    category_id = cat_response.json()["id"]

    product_data = {
        "name": "Ноутбук",
        "price": 1500.50,
        "sku": "LAPTOP-001",
        "category_id": category_id
    }
    
    prod_response = await client.post("/products/", json=product_data)
    
    assert prod_response.status_code in (200, 201)
    
    created_product = prod_response.json()
    assert created_product["name"] == "Ноутбук"
    assert created_product["price"] == 1500.50
    assert created_product["sku"] == "LAPTOP-001"
    assert created_product["category_id"] == category_id
    assert "id" in created_product