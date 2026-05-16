from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domain.entities.entities import Product
from src.domain.repositories.repositories import ProductRepository
from src.infrastructure.database.models import ProductModel
from src.infrastructure.mappers.mappers import ProductMapper


class ProductRepositoryImpl(ProductRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, product_id: int) -> Optional[Product]:
        query = select(ProductModel).where(ProductModel.id == product_id)
        result = await self.session.execute(query)
        orm_product = result.scalar_one_or_none()
        return ProductMapper.from_orm(orm_product) if orm_product else None

    async def get_by_sku(self, sku: str) -> Optional[Product]:
        query = select(ProductModel).where(ProductModel.sku == sku)
        result = await self.session.execute(query)
        orm_product = result.scalar_one_or_none()
        return ProductMapper.from_orm(orm_product) if orm_product else None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Product]:
        query = select(ProductModel).offset(skip).limit(limit)
        result = await self.session.execute(query)
        orm_products = result.scalars().all()
        return [ProductMapper.from_orm(p) for p in orm_products]

    async def create(self, product: Product) -> Product:
        orm_product = ProductModel(
            name=product.name,
            sku=product.sku.value,
            price=product.price.amount,
            category_id=product.category_id
        )
        self.session.add(orm_product)
        await self.session.flush()
        product.id = orm_product.id
        return product

    async def update(self, product: Product) -> Product:
        query = select(ProductModel).where(ProductModel.id == product.id)
        result = await self.session.execute(query)
        orm_product = result.scalar_one_or_none()

        if orm_product:
            orm_product.name = product.name
            orm_product.sku = product.sku.value
            orm_product.price = product.price.amount
            orm_product.category_id = product.category_id
            await self.session.flush()

        return product

    async def delete(self, product_id: int) -> bool:
        query = select(ProductModel).where(ProductModel.id == product_id)
        result = await self.session.execute(query)
        orm_product = result.scalar_one_or_none()

        if orm_product:
            await self.session.delete(orm_product)
            await self.session.flush()
            return True
        return False
