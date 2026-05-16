from src.domain.entities.entities import Product
from src.domain.factories.product_factory import ProductFactory
from src.domain.repositories.repositories import ProductRepository
from src.domain.errors.domain_errors import (
    DomainError, InvalidProductError, DuplicateSkuError
)


class CreateProductUseCase:
    """Use case for creating a product"""

    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository
        self.factory = ProductFactory(product_repository)

    async def execute(
        self,
        name: str,
        sku: str,
        price: float,
        category_id: int
    ) -> Product:
        """
        Create a product.

        Raises:
            InvalidProductError: if product data is invalid
            DuplicateSkuError: if SKU already exists
        """
        try:
            # Factory validates invariants
            product = await self.factory.create(
                name=name,
                sku=sku,
                price=price,
                category_id=category_id
            )

            # Save to repository
            created_product = await self.product_repository.create(product)
            return created_product

        except DomainError:
            raise  # Re-raise domain errors as-is
