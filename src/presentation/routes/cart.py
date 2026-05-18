from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.engine import db_helper
from src.infrastructure.repositories.cart_repository import CartRepositoryImpl
from src.infrastructure.repositories.product_repository import ProductRepositoryImpl
from src.infrastructure.repositories.stock_repository import StockRepositoryImpl
from src.application.use_cases.cart_use_cases import (
    GetCartUseCase,
    AddToCartUseCase,
    ClearCartUseCase,
)
from src.schemas.cart import CartItemAdd, CartItemResponse
from src.infrastructure.database.models import UserModel as User
from src.config.dependencies import get_current_user
from src.domain.entities.entities import Cart as DomainCart

router = APIRouter(prefix="/cart", tags=["Cart"])


async def get_cart_repository(db: AsyncSession = Depends(db_helper.get_db_session)):
    return CartRepositoryImpl(db)


async def get_product_repository(db: AsyncSession = Depends(db_helper.get_db_session)):
    return ProductRepositoryImpl(db)


async def get_stock_repository(db: AsyncSession = Depends(db_helper.get_db_session)):
    return StockRepositoryImpl(db)


@router.get("", status_code=status.HTTP_200_OK)
async def get_cart(
    cart_repo: CartRepositoryImpl = Depends(get_cart_repository),
    user: User = Depends(get_current_user),
):
    use_case = GetCartUseCase(cart_repo)
    try:
        cart = await use_case.execute(user.id)
        return {
            "items": [
                {"product_id": item.product_id, "quantity": int(item.quantity.value)}
                for item in cart.items
            ]
        }
    except Exception:
        return {"items": []}


@router.post(
    "/items", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED
)
async def add_item_to_cart(
    item_in: CartItemAdd,
    cart_repo: CartRepositoryImpl = Depends(get_cart_repository),
    product_repo: ProductRepositoryImpl = Depends(get_product_repository),
    stock_repo: StockRepositoryImpl = Depends(get_stock_repository),
    user: User = Depends(get_current_user),
):
    product = await product_repo.get_by_id(item_in.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    stock = await stock_repo.get_by_product_id(item_in.product_id)
    stock_qty = stock.quantity.value if stock else 0
    if stock_qty < item_in.quantity:
        raise HTTPException(
            status_code=400, detail=f"Not enough stock. Available: {int(stock_qty)}"
        )

    cart = await cart_repo.get_by_user_id(user.id)
    if not cart:
        cart = await cart_repo.create(DomainCart(id=0, user_id=user.id, items=[]))

    use_case = AddToCartUseCase(cart_repo)
    updated_cart = await use_case.execute(
        user_id=user.id,
        product_id=item_in.product_id,
        quantity=float(item_in.quantity),
        price=float(product.price.amount),
    )

    added_item = next(
        (i for i in updated_cart.items if i.product_id == item_in.product_id), None
    )

    if not added_item:
        raise HTTPException(status_code=500, detail="Failed to retrieve added item")

    return CartItemResponse(
            id=added_item.id, 
            product_id=added_item.product_id, 
            quantity=int(added_item.quantity.value)
        )


@router.delete("/clear", status_code=status.HTTP_200_OK)
async def clear_cart(
    cart_repo: CartRepositoryImpl = Depends(get_cart_repository),
    user: User = Depends(get_current_user),
):
    use_case = ClearCartUseCase(cart_repo)
    try:
        await use_case.execute(user.id)
        return {"message": "Cart cleared successfully"}
    except Exception:
        return {"message": "Cart is already empty"}
