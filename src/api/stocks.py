from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.engine import db_helper
from src.database.models import Stock, Product
from src.schemas.stocks import StockUpdate
from src.config.dependencies import get_current_user # Поки що так, пізніше додаси перевірку на адміна

router = APIRouter(
    prefix="/stocks",
    tags=["Stocks"]
)

@router.put("/{product_id}", status_code=status.HTTP_200_OK)
async def update_product_stock(
    product_id: int,
    stock_in: StockUpdate,
    db: AsyncSession = Depends(db_helper.get_db_session),
    user = Depends(get_current_user) # Тут в майбутньому має бути перевірка: if user.group != 'admin'
):
    # 1. Перевіряємо, чи існує такий продукт взагалі
    product_res = await db.execute(select(Product).where(Product.id == product_id))
    if not product_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Товар не знайдено.")

    # 2. Шукаємо запис у таблиці stocks
    stock_res = await db.execute(select(Stock).where(Stock.product_id == product_id))
    stock = stock_res.scalar_one_or_none()

    if stock:
        # Оновлюємо існуючий
        stock.quantity = stock_in.quantity
    else:
        # Створюємо новий запис, якщо його не було
        stock = Stock(product_id=product_id, quantity=stock_in.quantity)
        db.add(stock)

    await db.commit()
    return {"message": "Залишки оновлено", "product_id": product_id, "new_quantity": float(stock.quantity)}