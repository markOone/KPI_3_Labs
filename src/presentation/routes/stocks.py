from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.schemas.auth import UserResponseSchema
from src.database.engine import db_helper
from src.infrastructure.database.models import StockModel, ProductModel, UserModel
from src.schemas.stocks import StockUpdate
from src.config.dependencies import require_admin

router = APIRouter(prefix="/stocks", tags=["Stocks"])


@router.get("/{product_id}", status_code=status.HTTP_200_OK)
async def get_product_stock(
    product_id: int, db: AsyncSession = Depends(db_helper.get_db_session)
):
    res = await db.execute(
        select(StockModel).where(StockModel.product_id == product_id)
    )
    stock = res.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock information not found.")
    return {"product_id": product_id, "quantity": int(stock.quantity)}


@router.put("/{product_id}", status_code=status.HTTP_200_OK)
async def update_product_stock(
    product_id: int,
    stock_in: StockUpdate,
    db: AsyncSession = Depends(db_helper.get_db_session),
    admin: UserResponseSchema = Depends(require_admin),
):
    product_res = await db.execute(
        select(ProductModel).where(ProductModel.id == product_id)
    )
    if not product_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Product not found.")

    res = await db.execute(
        select(StockModel).where(StockModel.product_id == product_id)
    )
    stock = res.scalar_one_or_none()

    if stock:
        stock.quantity = stock_in.quantity
    else:
        stock = StockModel(product_id=product_id, quantity=stock_in.quantity)
        db.add(stock)

    await db.commit()
    return {
        "message": "Stock updated successfully",
        "product_id": product_id,
        "new_quantity": int(stock.quantity),
    }
