from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domain.entities.entities import Order
from src.domain.repositories.repositories import OrderRepository
from src.infrastructure.database.models import OrderModel
from src.infrastructure.mappers.mappers import OrderMapper


class OrderRepositoryImpl(OrderRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, order_id: int) -> Optional[Order]:
        query = select(OrderModel).where(OrderModel.id == order_id)
        result = await self.session.execute(query)
        orm_order = result.scalar_one_or_none()
        return OrderMapper.from_orm(orm_order) if orm_order else None

    async def get_by_user_id(self, user_id: int) -> List[Order]:
        query = select(OrderModel).where(OrderModel.user_id == user_id)
        result = await self.session.execute(query)
        orm_orders = result.scalars().all()
        return [OrderMapper.from_orm(o) for o in orm_orders]

    async def create(self, order: Order) -> Order:
        orm_order = OrderModel(
            user_id=order.user_id,
            status=order.status,
            total_price=order.total_price.amount,
            created_at=order.created_at
        )
        self.session.add(orm_order)
        await self.session.flush()
        order.id = orm_order.id
        return order

    async def update(self, order: Order) -> Order:
        query = select(OrderModel).where(OrderModel.id == order.id)
        result = await self.session.execute(query)
        orm_order = result.scalar_one_or_none()

        if orm_order:
            orm_order.status = order.status
            orm_order.total_price = order.total_price.amount
            await self.session.flush()

        return order
