from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload, joinedload

from src.domain.entities.entities import Cart, CartItem as DomainCartItem
from src.domain.repositories.repositories import CartRepository
from src.infrastructure.database.models import CartItemModel, CartModel
from src.infrastructure.mappers.mappers import CartMapper


class CartRepositoryImpl(CartRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: int):
        query = (
            select(CartModel)
            .options(selectinload(CartModel.items).joinedload(CartItemModel.product))
            .where(CartModel.user_id == user_id)
        )
        result = await self.session.execute(query)
        orm_cart = result.unique().scalar_one_or_none()

        if not orm_cart:
            return None

        items = [
            CartItem(
                id=i.id,
                product_id=i.product_id,
                quantity=Quantity(i.quantity),
                price=Money(float(i.product.price) if i.product else 0.0) 
            )
            for i in orm_cart.items
        ]

        return Cart(id=orm_cart.id, user_id=orm_cart.user_id, items=items)

    async def create(self, cart: Cart) -> Cart:
        orm_cart = CartModel(user_id=cart.user_id)
        self.session.add(orm_cart)
        await self.session.commit()
        await self.session.refresh(orm_cart)
        cart.id = orm_cart.id
        return cart

    async def update(self, cart: Cart) -> Cart:
        query = (
            select(CartModel)
            .options(selectinload(CartModel.items))
            .where(CartModel.id == cart.id)
        )
        result = await self.session.execute(query)
        orm_cart = result.unique().scalar_one_or_none()

        if orm_cart:
            orm_cart.items.clear()

            for item in cart.items:
                qty_val = item.quantity.value if hasattr(item.quantity, "value") else item.quantity
                orm_cart.items.append(
                    CartItemModel(
                        product_id=item.product_id,
                        quantity=qty_val
                    )
                )

            await self.session.commit()
            await self.session.refresh(orm_cart)

            from src.domain.value_objects.value_objects import Quantity, Money

            updated_items = []
            for orm_item in orm_cart.items:
                original_item = next((i for i in cart.items if i.product_id == orm_item.product_id), None)
                item_price = original_item.price if original_item else Money(0)

                updated_items.append(
                    DomainCartItem( 
                        id=orm_item.id,
                        product_id=orm_item.product_id,
                        quantity=Quantity(orm_item.quantity), 
                        price=item_price                    
                    )
                )
            cart.items = updated_items

        return cart

    async def delete(self, cart_id: int) -> bool:
        query = select(CartModel).where(CartModel.id == cart_id)
        result = await self.session.execute(query)
        orm_cart = result.scalar_one_or_none()

        if orm_cart:
            await self.session.delete(orm_cart)
            await self.session.commit()
            return True
        return False
