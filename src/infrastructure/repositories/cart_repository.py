from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from src.domain.entities.entities import Cart, CartItem as DomainCartItem
from src.domain.repositories.repositories import CartRepository
from src.infrastructure.database.models import CartItemModel, CartModel
from src.infrastructure.mappers.mappers import CartMapper


class CartRepositoryImpl(CartRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: int) -> Optional[Cart]:
        query = (
            select(CartModel)
            .options(selectinload(CartModel.items).selectinload(CartItemModel.product))
            .where(CartModel.user_id == user_id)
        )
        result = await self.session.execute(query)
        orm_cart = result.unique().scalar_one_or_none()
        return CartMapper.from_orm(orm_cart) if orm_cart else None

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
            await self.session.execute(
                delete(CartItemModel).where(CartItemModel.cart_id == orm_cart.id)
            )

            new_orm_items = [
                CartItemModel(
                    product_id=item.product_id,
                    quantity=(
                        item.quantity.value
                        if hasattr(item.quantity, "value")
                        else item.quantity
                    ),
                    cart_id=orm_cart.id,
                )
                for item in cart.items
            ]

            orm_cart.items = new_orm_items

            await self.session.commit()
            await self.session.refresh(orm_cart)

            updated_items = []
            for orm_item in orm_cart.items:
                updated_items.append(
                    DomainCartItem(
                        id=orm_item.id,
                        product_id=orm_item.product_id,
                        quantity=orm_item.quantity,
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
