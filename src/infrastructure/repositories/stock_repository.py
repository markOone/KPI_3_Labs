from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domain.entities.entities import Stock
from src.domain.repositories.repositories import StockRepository
from src.infrastructure.database.models import StockModel
from src.infrastructure.mappers.mappers import StockMapper


class StockRepositoryImpl(StockRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_product_id(self, product_id: int) -> Optional[Stock]:
        query = select(StockModel).where(StockModel.product_id == product_id)
        result = await self.session.execute(query)
        orm_stock = result.scalar_one_or_none()
        return StockMapper.from_orm(orm_stock) if orm_stock else None

    async def create(self, stock: Stock) -> Stock:
        orm_stock = StockModel(
            product_id=stock.product_id,
            quantity=int(stock.quantity.value)
        )
        self.session.add(orm_stock)
        await self.session.flush()
        stock.id = orm_stock.id
        return stock

    async def update(self, stock: Stock) -> Stock:
        query = select(StockModel).where(StockModel.id == stock.id)
        result = await self.session.execute(query)
        orm_stock = result.scalar_one_or_none()

        if orm_stock:
            orm_stock.quantity = int(stock.quantity.value)
            await self.session.flush()

        return stock
