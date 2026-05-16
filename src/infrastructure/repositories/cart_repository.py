from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domain.entities.entities import Cart
from src.domain.repositories.repositories import CartRepository
from src.infrastructure.database.models import CartModel
from src.infrastructure.mappers.mappers import CartMapper


class CartRepositoryImpl(CartRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: int) -> Optional[Cart]:
        query = select(CartModel).where(CartModel.user_id == user_id)
        result = await self.session.execute(query)
        orm_cart = result.scalar_one_or_none()
        return CartMapper.from_orm(orm_cart) if orm_cart else None

    async def create(self, cart: Cart) -> Cart:
        orm_cart = CartModel(
            user_id=cart.user_id
        )
        self.session.add(orm_cart)
        await self.session.flush()
        cart.id = orm_cart.id
        return cart

    async def update(self, cart: Cart) -> Cart:
        query = select(CartModel).where(CartModel.id == cart.id)
        result = await self.session.execute(query)
        orm_cart = result.scalar_one_or_none()

        if orm_cart:
            orm_cart.items = [item for item in cart.items]
            await self.session.flush()

        return cart

    async def delete(self, cart_id: int) -> bool:
        query = select(CartModel).where(CartModel.id == cart_id)
        result = await self.session.execute(query)
        orm_cart = result.scalar_one_or_none()

        if orm_cart:
            await self.session.delete(orm_cart)
            await self.session.flush()
            return True
        return False
