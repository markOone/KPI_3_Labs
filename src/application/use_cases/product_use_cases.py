from typing import List
from src.domain.entities.entities import Product
from src.domain.repositories.repositories import ProductRepository
from src.domain.errors.domain_errors import ProductNotFoundError
from src.domain.factories.product_factory import ProductFactory
from src.domain.errors.domain_errors import (
    DomainError, InvalidProductError, DuplicateSkuError
)

class GetProductUseCase:
    """Use case for getting a product by ID"""

    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    async def execute(self, product_id: int) -> Product:
        """
        Get a product by ID.

        Raises:
            ProductNotFoundError: if product not found
        """
        product = await self.product_repository.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError(f"Product with ID {product_id} not found")
        return product


class GetAllProductsUseCase:
    """Use case for getting all products"""

    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    async def execute(self, skip: int = 0, limit: int = 100) -> List[Product]:
        """Get all products with pagination"""
        return await self.product_repository.get_all(skip=skip, limit=limit)


class UpdateProductUseCase:
    """Use case for updating a product"""

    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    async def execute(
        self,
        product_id: int,
        name: str = None,
        sku: str = None,
        price: float = None,
        category_id: int = None
    ) -> Product:
        """
        Update a product.

        Raises:
            ProductNotFoundError: if product not found
        """
        product = await self.product_repository.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError(f"Product with ID {product_id} not found")

        # Check SKU uniqueness if changing SKU
        if sku and sku != product.sku.value:
            existing = await self.product_repository.get_by_sku(sku)
            if existing:
                from src.domain.errors.domain_errors import DuplicateSkuError
                raise DuplicateSkuError(f"Product with SKU '{sku}' already exists")

        # Update fields
        if name:
            product.name = name
        if sku:
            from src.domain.value_objects.value_objects import Sku
            product.sku = Sku(sku)
        if price:
            from src.domain.value_objects.value_objects import Money
            product.price = Money(price)
        if category_id:
            product.category_id = category_id

        # Validate and save
        product.validate()
        return await self.product_repository.update(product)


class DeleteProductUseCase:
    """Use case for deleting a product"""

    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    async def execute(self, product_id: int) -> bool:
        """
        Delete a product.

        Raises:
            ProductNotFoundError: if product not found
        """
        product = await self.product_repository.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError(f"Product with ID {product_id} not found")

        return await self.product_repository.delete(product_id)

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
