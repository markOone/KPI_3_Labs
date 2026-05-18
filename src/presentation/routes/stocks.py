from fastapi import APIRouter, Depends, HTTPException, status
from src.schemas.auth import UserResponseSchema
from src.application.use_cases.stock_use_cases import (
    GetStockUseCase,
    UpdateStockUseCase,
)
from src.domain.repositories.repositories import StockRepository
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
    admin: UserResponseSchema = Depends(require_admin),
):
    use_case = UpdateStockUseCase(stock_repo)
    await use_case.execute(product_id, stock_in.quantity)

    return HTTPException(
        status_code=status.HTTP_200_OK, detail="Stock updated successfully."
    )
