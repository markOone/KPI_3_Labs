from domain.repositories.repositories import StockRepository


class UpdateStockUseCase:
    def __init__(self, stock_repository: StockRepository):
        self.stock_repository = stock_repository

    async def execute(self, product_id: int, quantity: int):
        stock = await self.stock_repository.get_stock_by_product_id(product_id)
        if not stock:
            raise ValueError("Stock not found for the given product ID")
        stock.quantity = quantity
        await self.stock_repository.update_stock(stock)


class GetStockUseCase:
    def __init__(self, stock_repository: StockRepository):
        self.stock_repository = stock_repository

    async def execute(self, product_id: int) -> int:
        stock = await self.stock_repository.get_by_product_id(product_id)
        if not stock:
            raise ValueError("Stock not found for the given product ID")
        return stock.quantity.value
