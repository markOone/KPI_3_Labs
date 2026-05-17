from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.auth import UserResponseSchema
from src.database.engine import db_helper
from src.infrastructure.repositories.order_repository import OrderRepositoryImpl
from src.infrastructure.repositories.cart_repository import CartRepositoryImpl
from src.infrastructure.repositories.product_repository import ProductRepositoryImpl
from src.application.commands.order_commands import ProcessCheckoutCommand
from src.application.commands.order_command_handlers import ProcessCheckoutCommandHandler
from src.application.queries.order_queries import GetOrderQuery, GetUserOrdersQuery
from src.application.queries.order_queries_handlers import GetOrderQueryHandler, GetUserOrdersQueryHandler
from src.domain.errors.domain_errors import DomainError
from src.schemas.orders import OrderResponse
from src.config.dependencies import get_current_user
from src.infrastructure.database.models import UserModel

router = APIRouter(prefix="/orders", tags=["Orders"])


async def get_order_repository(db: AsyncSession = Depends(db_helper.get_db_session)):
    return OrderRepositoryImpl(db)


async def get_cart_repository(db: AsyncSession = Depends(db_helper.get_db_session)):
    return CartRepositoryImpl(db)


async def get_product_repository(db: AsyncSession = Depends(db_helper.get_db_session)):
    return ProductRepositoryImpl(db)


@router.post(
    "/checkout", response_model=OrderResponse, status_code=status.HTTP_201_CREATED
)
async def process_checkout(
    db: AsyncSession = Depends(db_helper.get_db_session),
    user: UserModel = Depends(get_current_user),
    order_repo: OrderRepositoryImpl = Depends(get_order_repository),
    cart_repo: CartRepositoryImpl = Depends(get_cart_repository),
    product_repo: ProductRepositoryImpl = Depends(get_product_repository),
):
    handler = ProcessCheckoutCommandHandler(cart_repo, product_repo, order_repo)
    try:
        command = ProcessCheckoutCommand(user_id=user.id)
        order_id = await handler.handle(command)

        order = await order_repo.get_by_id(order_id)
        return OrderResponse(
            id=order.id,
            user_id=order.user_id,
            status=order.status,
            total_price=float(order.total_price.amount),
            created_at=order.created_at,
            items=[
                {
                    "id": i.id,
                    "product_id": i.product_id,
                    "quantity": float(i.quantity.value),
                    "price_at_purchase": float(i.price_at_purchase.amount),
                }
                for i in order.items
            ],
        )

    except DomainError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    order_repo: OrderRepositoryImpl = Depends(get_order_repository),
    user: UserModel = Depends(get_current_user),
):
    handler = GetOrderQueryHandler(order_repo)
    try:
        query = GetOrderQuery(order_id=order_id)
        return await handler.handle(query)
    except DomainError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/orders", response_model=list[OrderResponse])
async def get_user_orders(
    order_repo: OrderRepositoryImpl = Depends(get_order_repository),
    user: UserModel = Depends(get_current_user),
):
    handler = GetUserOrdersQueryHandler(order_repo)
    try:
        query = GetUserOrdersQuery(user_id=user.id)
        return await handler.handle(query)
    except DomainError as e:
        raise HTTPException(status_code=400, detail=str(e))
