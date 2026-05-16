import pytest
from src.domain.factories.product_factory import ProductFactory
from src.domain.entities.entities import Product
from src.domain.value_objects.value_objects import Sku, Money
from src.domain.errors.domain_errors import DuplicateSkuError, InvalidProductError
from src.domain.repositories.repositories import ProductRepository

class FakeProductRepository(ProductRepository):
    def __init__(self):
        self.products = []

    async def get_by_sku(self, sku: str):
        for p in self.products:
            if p.sku.value == sku:
                return p
        return None

    async def get_by_id(self, product_id: int): pass
    async def get_all(self, skip: int = 0, limit: int = 100): pass
    async def create(self, product: Product): pass
    async def update(self, product: Product): pass
    async def delete(self, product_id: int): pass


class TestProductFactory:
    """Unit tests for Product Domain Factory using Fake Repository"""

    @pytest.mark.asyncio
    async def test_factory_creates_valid_product(self):
        repo = FakeProductRepository()
        factory = ProductFactory(repository=repo)

        product = await factory.create(
            name="Відьмак 3",
            sku="W3-GAME-01",
            price=800.0,
            category_id=1
        )

        assert isinstance(product, Product)
        assert product.name == "Відьмак 3"
        assert product.sku.value == "W3-GAME-01"
        assert product.price.amount == 800.0

    @pytest.mark.asyncio
    async def test_factory_fails_on_duplicate_sku(self):
        repo = FakeProductRepository()
        existing_product = Product(
            id=1, 
            name="Стара гра", 
            sku=Sku("W3-GAME-01"), 
            price=Money(100), 
            category_id=1
        )
        repo.products.append(existing_product)
        
        factory = ProductFactory(repository=repo)

        with pytest.raises(DuplicateSkuError) as exc_info:
            await factory.create(
                name="Нова гра",
                sku="W3-GAME-01",
                price=800.0,
                category_id=1
            )
        assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_factory_fails_on_invalid_price(self):
        repo = FakeProductRepository()
        factory = ProductFactory(repository=repo)

        with pytest.raises(InvalidProductError):
            await factory.create(
                name="Безкоштовна гра",
                sku="FREE-001",
                price=0.0, 
                category_id=1
            )