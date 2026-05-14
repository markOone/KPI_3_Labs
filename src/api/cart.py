from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.database.engine import db_helper
from src.database.models import Cart, CartItem, Product
from src.schemas.cart import CartItemAdd, CartItemResponse

from src.config.dependencies import get_current_user

router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)

@router.post("/items", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
async def add_item_to_cart(
    item_in: CartItemAdd,
    db: AsyncSession = Depends(db_helper.get_db_session),
    user = Depends(get_current_user) # Тут має бути твоя авторизація
):
    # 1. Перевіряємо, чи існує такий товар взагалі
    product_query = select(Product).where(Product.id == item_in.product_id)
    product_result = await db.execute(product_query)
    if not product_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не знайдено.")

    # 2. Шукаємо корзину користувача (разом з її айтемами)
# 2. Шукаємо корзину користувача (разом з її айтемами)
    cart_query = select(Cart).options(joinedload(Cart.items)).where(Cart.user_id == user.id)
    cart_result = await db.execute(cart_query)
    cart = cart_result.unique().scalar_one_or_none()

    existing_item = None

    # Якщо корзини немає - створюємо нову
    if not cart:
        cart = Cart(user_id=user.id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)
        # Оскільки корзина нова, existing_item точно залишається None
        # і ми НЕ звертаємося до cart.items, уникаючи помилки MissingGreenlet
    else:
        # Якщо корзина вже була, ми підвантажили її items через joinedload.
        # Тому тут можна безпечно шукати товар.
        existing_item = next((item for item in cart.items if item.product_id == item_in.product_id), None)

    # 3. Оновлюємо або створюємо CartItem
    if existing_item:
        # Якщо є - просто збільшуємо кількість
        existing_item.quantity += item_in.quantity
        updated_item = existing_item
    else:
        # Якщо ні - створюємо новий запис
        new_cart_item = CartItem(
            cart_id=cart.id,
            product_id=item_in.product_id,
            quantity=item_in.quantity
        )
        db.add(new_cart_item)
        updated_item = new_cart_item

    await db.commit()
    await db.refresh(updated_item)
    return updated_item