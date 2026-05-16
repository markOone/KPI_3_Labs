from src.domain.entities.entities import Product
from src.domain.value_objects.value_objects import Sku, Money
from src.domain.errors.domain_errors import DuplicateSkuError, InvalidProductError
from src.domain.repositories.repositories import ProductRepository


class ProductFactory:
    """Factory for creating Product domain objects with invariant validation"""

    def __init__(self, repository: ProductRepository):
        self.repository = repository

    async def create(
        self,
        name: str,
        sku: str,
        price: float,
        category_id: int
    ) -> Product:
        """Create a new product with validation"""
        # Simple invariants (no DB needed)
        if not name or len(name) == 0:
            raise InvalidProductError("Product name cannot be empty")
        if price <= 0:
            raise InvalidProductError("Product price must be positive")

        # Complex invariants (need DB)
        existing_product = await self.repository.get_by_sku(sku)
        if existing_product:
            raise DuplicateSkuError(f"Product with SKU '{sku}' already exists")

        # Create domain object
        return Product(
            id=0,  # Will be assigned by repository
            name=name,
            sku=Sku(sku),
            price=Money(price),
            category_id=category_id
        )
