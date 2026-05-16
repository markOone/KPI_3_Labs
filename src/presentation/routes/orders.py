from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.engine import db_helper
from src.infrastructure.repositories.order_repository import OrderRepositoryImpl
from src.infrastructure.repositories.cart_repository import CartRepositoryImpl
from src.infrastructure.repositories.stock_repository import StockRepositoryImpl
from src.application.use_cases.order_use_cases import CreateOrderUseCase
from src.domain.errors.domain_errors import DomainError
from src.schemas.orders import OrderResponse
from src.config.dependencies import get_current_user
from src.database.models import User

router = APIRouter(prefix="/orders", tags=["Orders"])

async def get_order_repository(db: AsyncSession = Depends(db_helper.get_db_session)):
    return OrderRepositoryImpl(db)

async def get_cart_repository(db: AsyncSession = Depends(db_helper.get_db_session)):
    return CartRepositoryImpl(db)

@router.post("/checkout", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def process_checkout(
    db: AsyncSession = Depends(db_helper.get_db_session),
    user: User = Depends(get_current_user),
    order_repo: OrderRepositoryImpl = Depends(get_order_repository),
    cart_repo: CartRepositoryImpl = Depends(get_cart_repository)
):
    cart = await cart_repo.get_by_user_id(user.id)
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")
        
    use_case = CreateOrderUseCase(order_repo)
    try:
        items_data = [(item.product_id, item.quantity.value, item.price.amount) for item in cart.items]
        order = await use_case.execute(
            user_id=user.id,
            items=items_data,
            total_price=cart.total_price().amount
        )
        return order
    except DomainError as e:
        raise HTTPException(status_code=400, detail=str(e))