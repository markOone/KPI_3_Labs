from fastapi import APIRouter, Depends, HTTPException, status
from domain.repositories.repositories import CartRepository, OrderRepository
from src.application.use_cases.order_use_cases import CreateOrderUseCase
from src.domain.errors.domain_errors import DomainError
from src.schemas.orders import OrderResponse
from src.config.dependencies import (
    get_cart_repository,
    get_current_user,
    get_order_repository,
)
from src.infrastructure.database.models import UserModel as User

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "/checkout", response_model=OrderResponse, status_code=status.HTTP_201_CREATED
)
async def process_checkout(
    user: User = Depends(get_current_user),
    order_repo: OrderRepository = Depends(get_order_repository),
    cart_repo: CartRepository = Depends(get_cart_repository),
):
    cart = await cart_repo.get_by_user_id(user.id)
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    use_case = CreateOrderUseCase(order_repo, cart_repo)
    try:
        items_data = [
            (item.product_id, item.quantity.value, item.price.amount)
            for item in cart.items
        ]

        order = await use_case.execute(
            user_id=user.id,
            items=items_data,
            total_price=cart.total_price().amount,
            cart_id=cart.id,
        )

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
