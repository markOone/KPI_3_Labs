from src.application.commands.product_commands import (
    CreateProductCommand,
    UpdateProductCommand,
    DeleteProductCommand
)
from src.domain.repositories.repositories import ProductRepository
from src.domain.factories.product_factory import ProductFactory
from src.domain.errors.domain_errors import ProductNotFoundError, DuplicateSkuError
from src.domain.value_objects.value_objects import Sku, Money

class CreateProductCommandHandler:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository
        self.factory = ProductFactory(product_repository)

    async def handle(self, command: CreateProductCommand) -> int:
        product = await self.factory.create(
            name=command.name,
            sku=command.sku,
            price=command.price,
            category_id=command.category_id
        )
        created_product = await self.product_repository.create(product)
        return created_product.id


class UpdateProductCommandHandler:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    async def handle(self, command: UpdateProductCommand) -> None:
        product = await self.product_repository.get_by_id(command.product_id)
        if not product:
            raise ProductNotFoundError(f"Product with ID {command.product_id} not found")

        if command.sku and command.sku != product.sku.value:
            existing = await self.product_repository.get_by_sku(command.sku)
            if existing:
                raise DuplicateSkuError(f"Product with SKU '{command.sku}' already exists")

        if command.name:
            product.name = command.name
        if command.sku:
            product.sku = Sku(command.sku)
        if command.price:
            product.price = Money(command.price)
        if command.category_id:
            product.category_id = command.category_id

        product.validate()
        await self.product_repository.update(product)


class DeleteProductCommandHandler:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    async def handle(self, command: DeleteProductCommand) -> None:
        product = await self.product_repository.get_by_id(command.product_id)
        if not product:
            raise ProductNotFoundError(f"Product with ID {command.product_id} not found")

        await self.product_repository.delete(command.product_id)