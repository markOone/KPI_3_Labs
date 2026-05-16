from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from loguru import logger
from src.database.engine import db_helper
from src.database.models import Cart, CartItem, Product, User
from src.schemas.cart import CartItemAdd, CartItemResponse

from src.config.dependencies import get_current_user

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("/", status_code=status.HTTP_200_OK)
async def get_cart(
    db: AsyncSession = Depends(db_helper.get_db_session),
    user: User = Depends(get_current_user),
):
    cart_query = (
        select(Cart).options(joinedload(Cart.items)).where(Cart.user_id == user.id)
    )
    cart_result = await db.execute(cart_query)
    cart = cart_result.unique().scalar_one_or_none()

    if not cart:
        return {"items": []}

    return {
        "items": [
            {"product_id": item.product_id, "quantity": item.quantity}
            for item in cart.items
        ]
    }


@router.post(
    "/items", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED
)
async def add_item_to_cart(
    item_in: CartItemAdd,
    db: AsyncSession = Depends(db_helper.get_db_session),
    user: User = Depends(get_current_user),
):
    product_query = (
        select(Product)
        .options(joinedload(Product.stock))
        .where(Product.id == item_in.product_id)
    )
    product_result = await db.execute(product_query)
    product = product_result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )

    stock_quantity = product.stock.quantity if product.stock else 0
    if stock_quantity < item_in.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Not enough stock. Available: {int(stock_quantity)}",
        )

    cart_query = (
        select(Cart).options(joinedload(Cart.items)).where(Cart.user_id == user.id)
    )
    cart_result = await db.execute(cart_query)
    cart = cart_result.scalar_one_or_none()

    if not cart:
        cart = Cart(user_id=user.id)
        db.add(cart)
        await db.flush()

    existing_item = next(
        (item for item in cart.items if item.product_id == item_in.product_id), None
    )

    if existing_item:
        existing_item.quantity += item_in.quantity
        updated_item = existing_item
    else:
        new_cart_item = CartItem(
            cart_id=cart.id,
            product_id=item_in.product_id,
            quantity=item_in.quantity,
        )
        db.add(new_cart_item)
        updated_item = new_cart_item

    try:
        await db.commit()
        await db.refresh(updated_item)
        return updated_item
    except Exception as e:
        await db.rollback()
        logger.error(f"Add to cart error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add item to cart",
        )
