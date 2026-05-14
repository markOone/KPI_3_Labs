from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert
from sqlalchemy.orm import joinedload
from decimal import Decimal
from datetime import datetime, timezone

from src.database.engine import db_helper
from src.database.models import Cart, CartItem, Order, OrderItem, Stock, Product
from src.schemas.orders import OrderResponse
from src.config.dependencies import get_current_user

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)

@router.post("/checkout", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def process_checkout(
    db: AsyncSession = Depends(db_helper.get_db_session),
    user = Depends(get_current_user)
):
    # Витягуємо ID відразу
    u_id = user.id
    
    # ПЕРША ВАЖЛИВА ДІЯ: Від'єднуємо юзера від сесії, щоб він не спамив запитами
    db.expunge(user) 

    # 1. Отримуємо кошик
    cart_res = await db.execute(select(Cart).where(Cart.user_id == u_id))
    cart = cart_res.scalar_one_or_none()

    if not cart:
        raise HTTPException(status_code=400, detail="Кошик порожній")

    # 2. Отримуємо товари
    items_res = await db.execute(
        select(CartItem)
        .options(joinedload(CartItem.product))
        .where(CartItem.cart_id == cart.id)
    )
    cart_items = items_res.scalars().all()

    try:
        # 3. Блокуємо сток
        p_ids = [i.product_id for i in cart_items]
        stock_res = await db.execute(
            select(Stock).where(Stock.product_id.in_(p_ids)).with_for_update()
        )
        stock_map = {s.product_id: s for s in stock_res.scalars().all()}

        total = Decimal("0.0")
        items_data = []

        for ci in cart_items:
            s = stock_map.get(ci.product_id)
            if not s or s.quantity < ci.quantity:
                await db.rollback()
                raise HTTPException(status_code=409, detail="Недостатньо товару")

            s.quantity -= ci.quantity
            p = Decimal(str(ci.product.price))
            total += p * Decimal(str(ci.quantity))
            
            items_data.append({
                "product_id": ci.product_id,
                "quantity": float(ci.quantity),
                "price_at_purchase": float(p)
            })

        # 4. Інсертимо через Core (найбезпечніший шлях)
        now = datetime.now(timezone.utc)
        order_stmt = insert(Order).values(
            user_id=u_id, status="created", total_price=total, created_at=now
        ).returning(Order.id)
        
        o_res = await db.execute(order_stmt)
        new_order_id = o_res.scalar_one()

        for d in items_data:
            d["order_id"] = new_order_id
        
        await db.execute(insert(OrderItem).values(items_data))
        await db.execute(delete(CartItem).where(CartItem.cart_id == cart.id))

        # 5. ФІНАЛЬНИЙ СЛОВНИК
        resp_dict = {
            "id": new_order_id,
            "user_id": u_id,
            "status": "created",
            "total_price": float(total),
            "created_at": now,
            "items": items_data
        }

        await db.commit()
        
        # ДРУГА ВАЖЛИВА ДІЯ: Очищуємо сесію повністю перед поверненням
        db.expunge_all()

        return resp_dict

    except Exception as e:
        await db.rollback()
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=f"Критична помилка: {str(e)}")