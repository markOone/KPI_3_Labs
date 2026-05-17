from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.auth import UserResponseSchema
from src.database.engine import db_helper
from src.infrastructure.repositories.cart_repository import CartRepositoryImpl
from src.infrastructure.repositories.product_repository import ProductRepositoryImpl
from src.infrastructure.repositories.stock_repository import StockRepositoryImpl
from src.application.commands.cart_commands import (
    AddToCartCommand,
    ClearCartCommand,
)
from src.application.commands.cart_handlers import (
    AddToCartCommandHandler,
    ClearCartCommandHandler,
)
from src.application.queries.cart_queries import GetCartQuery
from src.application.queries.cart_handlers import GetCartQueryHandler
from src.schemas.cart import CartItemAdd, CartItemResponse
from src.database.models import User
from src.config.dependencies import get_current_user
from src.domain.entities.entities import Cart as DomainCart

router = APIRouter(prefix="/cart", tags=["Cart"])


async def get_cart_repository(db: AsyncSession = Depends(db_helper.get_db_session)):
    return CartRepositoryImpl(db)


async def get_product_repository(db: AsyncSession = Depends(db_helper.get_db_session)):
    return ProductRepositoryImpl(db)


@router.get("", status_code=status.HTTP_200_OK)
async def get_cart(
    cart_repo: CartRepositoryImpl = Depends(get_cart_repository),
    user: User = Depends(get_current_user),
):
    query = GetCartQuery(user_id=user.id)
    handler = GetCartQueryHandler(cart_repo)
    try:
        cart = await handler.handle(query)
        return {
            "items": [
                {"product_id": item.product_id, "quantity": int(item.quantity.value)}
                for item in cart.items
            ]
        }
    except Exception:
        return {"items": []}


@router.post("/items", status_code=status.HTTP_201_CREATED)
async def add_item_to_cart(
    item_in: CartItemAdd,
    cart_repo: CartRepositoryImpl = Depends(get_cart_repository),
    user: UserResponseSchema = Depends(get_current_user),
):
    command = AddToCartCommand(
        user_id=user.id, product_id=item_in.product_id, quantity=float(item_in.quantity)
    )

    handler = AddToCartCommandHandler(cart_repo)

    try:
        await handler.handle(command)
        return HTTPException(
            status_code=status.HTTP_204_NO_CONTENT, detail="Item added to cart"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/clear", status_code=status.HTTP_200_OK)
async def clear_cart(
    cart_repo: CartRepositoryImpl = Depends(get_cart_repository),
    user: User = Depends(get_current_user),
):
    command = ClearCartCommand(user_id=user.id)
    handler = ClearCartCommandHandler(cart_repo)
    try:
        await handler.handle(command)
        return {"message": "Cart cleared successfully"}
    except Exception:
        return {"message": "Cart is already empty"}
