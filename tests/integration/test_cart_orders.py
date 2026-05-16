import pytest
from httpx import AsyncClient
from src.main import app
from src.config.dependencies import require_admin

@pytest.mark.asyncio
async def test_full_checkout_flow(client: AsyncClient):
    reg_res = await client.post("/auth/register", json={
        "username": "shopper", 
        "email": "shop@test.com", 
        "password": "secure_password_123"
    })
    assert reg_res.status_code in (200, 201)

    login_res = await client.post("/auth/login", data={
        "username": "shopper", 
        "password": "secure_password_123"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cat_res = await client.post("/categories/", json={"name": "Ігри"})
    assert cat_res.status_code in (200, 201)
    category_id = cat_res.json()["id"]

    prod_res = await client.post("/products/", json={
        "name": "Відьмак 3",
        "price": 800.00,
        "sku": "W3-GAME-01",
        "category_id": category_id
    })
    assert prod_res.status_code in (200, 201)
    product_id = prod_res.json()["id"]

    app.dependency_overrides[require_admin] = lambda: None
    stock_res = await client.put(f"/stocks/{product_id}", json={"quantity": 10}, headers=headers)
    assert stock_res.status_code == 200
    app.dependency_overrides.pop(require_admin, None)

    cart_item = {
        "product_id": product_id,
        "quantity": 2
    }
    cart_res = await client.post("/cart/items", json=cart_item, headers=headers)
    assert cart_res.status_code in (200, 201), f"Помилка додавання в кошик: {cart_res.text}"

    get_cart_res = await client.get("/cart", headers=headers)
    assert get_cart_res.status_code == 200
    assert len(get_cart_res.json()["items"]) > 0

    order_res = await client.post("/orders/checkout", headers=headers)
    assert order_res.status_code in (200, 201), f"Помилка оформлення замовлення: {order_res.text}"
    
    order_data = order_res.json()
    assert order_data["status"] == "created"
    assert float(order_data["total_price"]) == 1600.00

    empty_cart_res = await client.get("/cart", headers=headers)
    assert empty_cart_res.status_code == 200
    assert len(empty_cart_res.json()["items"]) == 0