from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.database.engine import db_helper
from src.database.models import Cart, CartItem, Order, OrderItem, Stock, Product
from src.schemas.orders import OrderResponse

from src.config.dependencies import get_current_user

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)

@router.post("/checkout", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def process_checkout(
    db: AsyncSession = Depends(db_helper.get_db_session),
    user = Depends(get_current_user) # Тут має бути твоя авторизація
):

    # 1. Отримуємо корзину зі зв'язками: Cart -> CartItems -> Product
    # Це критично в асинхронній алхімії, щоб уникнути помилок підвантаження
    cart_query = (
        select(Cart)
        .where(Cart.user_id == user.id)
        .options(
            joinedload(Cart.items).joinedload(CartItem.product)
        )
    )
    result = await db.execute(cart_query)
    cart = result.unique().scalar_one_or_none()

    if not cart or not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Спроба оформити порожній кошик."
        )

    product_ids = [item.product_id for item in cart.items]

    try:
        # 2. БЛОКУЄМО ЗАЛИШКИ (Pessimistic Locking)
        # Ніхто інший не зможе змінити ці залишки, поки ми не зробимо commit() або rollback()
        stock_query = (
            select(Stock)
            .where(Stock.product_id.in_(product_ids))
            .with_for_update()
        )
        stock_result = await db.execute(stock_query)
        stocks = stock_result.scalars().all()
        
        # Робимо словник {product_id: об'єкт Stock} для швидкого доступу
        stock_map = {s.product_id: s for s in stocks}

        total_order_price = 0.0
        order_items_to_create = []

        # 3. Перевіряємо наявність та формуємо позиції замовлення
        for cart_item in cart.items:
            stock = stock_map.get(cart_item.product_id)
            
            # Якщо залишку немає або його менше, ніж хоче юзер - конфлікт
            if not stock or stock.quantity < cart_item.quantity:
                await db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, 
                    detail=f"Недостатньо товару '{cart_item.product.name}'. Доступно: {stock.quantity if stock else 0}"
                )

            # Списуємо зі складу
            stock.quantity -= cart_item.quantity
            
            # Рахуємо фінансову частину (фіксуємо ціну товару з каталогу на момент покупки)
            item_price = float(cart_item.product.price)
            total_order_price += item_price * float(cart_item.quantity)

            order_items_to_create.append(
                OrderItem(
                    product_id=cart_item.product_id,
                    quantity=cart_item.quantity,
                    price_at_purchase=item_price # Фіксація ціни!
                )
            )

        # 4. Створюємо фінальне замовлення
        new_order = Order(
            user_id=user.id,
            status="created",
            total_price=total_order_price,
            items=order_items_to_create
        )
        db.add(new_order)

        # 5. Очищаємо кошик 
        # Оскільки ми використовували cascade="all, delete-orphan", ми можемо просто 
        # видалити CartItems, і вони зникнуть з бази
        for item in cart.items:
            await db.delete(item)

        # 6. Зберігаємо всі зміни (транзакція закривається, блокування стоку знімається)
        await db.commit()
        
        # Підвантажуємо створене замовлення з його айтемами для красивої відповіді
        await db.refresh(new_order)
        
        # В асинхронній алхімії, щоб повернути Pydantic модель з вкладеними items, 
        # нам треба їх явно підвантажити, якщо вони не були завантажені при refresh
        final_order_query = (
            select(Order)
            .where(Order.id == new_order.id)
            .options(joinedload(Order.items))
        )
        final_res = await db.execute(final_order_query)
        complete_order = final_res.unique().scalar_one()

        return complete_order

    except HTTPException:
        # Перекидаємо наші HTTP помилки (наприклад, 409) далі
        raise
    except Exception as e:
        # У разі будь-якої іншої непередбаченої помилки - відкочуємо зміни
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка при створенні замовлення: {str(e)}"
        )