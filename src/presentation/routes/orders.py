from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload
from decimal import Decimal
from datetime import datetime, timezone
from src.database.engine import db_helper
from src.database.models import Cart, CartItem, Order, OrderItem, Stock, User
from src.schemas.orders import OrderResponse
from src.config.dependencies import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.get("/", status_code=status.HTTP_200_OK)
async def get_user_orders(db: AsyncSession = Depends(db_helper.get_db_session), user: User = Depends(get_current_user)):
    query = select(Order).options(joinedload(Order.items).joinedload(OrderItem.product)).where(Order.user_id == user.id).order_by(Order.created_at.desc())
    res = await db.execute(query)
    orders = res.unique().scalars().all()
    return [
        {
            "id": order.id,
            "user_id": order.user_id,
            "status": order.status,
            "total_price": float(order.total_price),
            "created_at": order.created_at,
            "items": [
                {
                    "product_id": item.product_id,
                    "quantity": float(item.quantity),
                    "price_at_purchase": float(item.price_at_purchase)
                } for item in order.items
            ]
        } for order in orders
    ]

@router.post("/checkout", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def process_checkout(db: AsyncSession = Depends(db_helper.get_db_session), user: User = Depends(get_current_user)):
    cart_res = await db.execute(select(Cart).options(joinedload(Cart.items).joinedload(CartItem.product)).where(Cart.user_id == user.id))
    cart = cart_res.unique().scalar_one_or_none()
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    p_ids = [item.product_id for item in cart.items]
    stock_res = await db.execute(select(Stock).where(Stock.product_id.in_(p_ids)).with_for_update())
    stock_map = {s.product_id: s for s in stock_res.scalars().all()}

    total_price = Decimal("0.0")
    order_items_payload = []

    for item in cart.items:
        stock = stock_map.get(item.product_id)
        if not stock or stock.quantity < item.quantity:
            raise HTTPException(status_code=409, detail=f"Product {item.product.name} is out of stock")
        stock.quantity -= item.quantity
        item_price = Decimal(str(item.product.price))
        total_price += item_price * Decimal(str(item.quantity))
        order_items_payload.append({"product_id": item.product_id, "quantity": item.quantity, "price_at_purchase": item_price})

    new_order = Order(user_id=user.id, status="created", total_price=total_price, created_at=datetime.now(timezone.utc))
    db.add(new_order)
    await db.flush()

    for data in order_items_payload:
        db.add(OrderItem(order_id=new_order.id, product_id=data["product_id"], quantity=data["quantity"], price_at_purchase=data["price_at_purchase"]))

    await db.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
    await db.commit()
    await db.refresh(new_order)
    return new_order