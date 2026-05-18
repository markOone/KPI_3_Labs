from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from application.use_cases.stock_use_cases import GetStockUseCase, UpdateStockUseCase
from domain.repositories.repositories import CartRepository, StockRepository
from presentation.routes.orders import get_cart_repository
from src.infrastructure.engine import db_helper
from src.infrastructure.database.models import Stock, Product, User
from src.schemas.stocks import StockUpdate
from src.config.dependencies import get_stock_repository, require_admin

router = APIRouter(prefix="/stocks", tags=["Stocks"])


@router.get("/{product_id}", status_code=status.HTTP_200_OK)
async def get_product_stock(
    product_id: int, stock_repo: StockRepository = Depends(get_stock_repository)
):
    use_case = GetStockUseCase(stock_repo)
    return await use_case.execute(product_id)


@router.put("/{product_id}", status_code=status.HTTP_200_OK)
async def update_product_stock(
    product_id: int,
    stock_in: StockUpdate,
    stock_repo: StockRepository = Depends(get_stock_repository),
    admin: User = Depends(require_admin),
):
    use_case = UpdateStockUseCase(stock_repo)
    await use_case.execute(product_id)

    return HTTPException(
        status_code=status.HTTP_200_OK, detail="Stock updated successfully."
    )
