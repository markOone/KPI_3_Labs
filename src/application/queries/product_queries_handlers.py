from typing import List
from src.application.queries.product_queries import GetProductQuery, GetAllProductsQuery
from src.domain.repositories.repositories import ProductRepository
from src.domain.errors.domain_errors import ProductNotFoundError
from src.schemas.products import ProductResponse  

class GetProductQueryHandler:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    async def handle(self, query: GetProductQuery) -> ProductResponse:
        product = await self.product_repository.get_by_id(query.product_id)
        if not product:
            raise ProductNotFoundError(f"Product with ID {query.product_id} not found")
        
        return ProductResponse(
            id=product.id,
            name=product.name,
            sku=product.sku.value,
            price=product.price.amount,
            category_id=product.category_id
        )

class GetAllProductsQueryHandler:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    async def handle(self, query: GetAllProductsQuery) -> List[ProductResponse]:
        products = await self.product_repository.get_all(skip=query.skip, limit=query.limit)
        return [
            ProductResponse(
                id=p.id,
                name=p.name,
                sku=p.sku.value,
                price=p.price.amount,
                category_id=p.category_id
            ) for p in products
        ]