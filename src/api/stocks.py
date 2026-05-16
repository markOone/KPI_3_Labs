from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.engine import db_helper
from src.database.models import Stock, Product, User
from src.schemas.stocks import StockUpdate
from src.config.dependencies import (
    require_admin,
)
from loguru import logger

router = APIRouter(prefix="/stocks", tags=["Stocks"])


@router.put("/{product_id}", status_code=status.HTTP_200_OK)
async def update_product_stock(
    product_id: int,
    stock_in: StockUpdate,
    db: AsyncSession = Depends(db_helper.get_db_session),
    admin: User = Depends(require_admin),  # only admin can update stock
):
    if stock_in.quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock quantity cannot be negative",
        )

    product_res = await db.execute(select(Product).where(Product.id == product_id))
    if not product_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )

    try:
        stock_res = await db.execute(
            select(Stock).where(Stock.product_id == product_id)
        )
        stock = stock_res.scalar_one_or_none()

        if stock:
            stock.quantity = stock_in.quantity
        else:
            stock = Stock(product_id=product_id, quantity=stock_in.quantity)
            db.add(stock)

        await db.commit()
        return {
            "message": "Stock updated successfully",
            "product_id": product_id,
            "new_quantity": int(stock.quantity),
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Stock update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка при оновленні залишків",
        )
