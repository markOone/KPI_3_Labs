from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.entities.entities import Product, Stock, User, Cart, Order


class ProductRepository(ABC):
    """Product repository interface"""

    @abstractmethod
    async def get_by_id(self, product_id: int) -> Optional[Product]:
        pass

    @abstractmethod
    async def get_by_sku(self, sku: str) -> Optional[Product]:
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Product]:
        pass

    @abstractmethod
    async def create(self, product: Product) -> Product:
        pass

    @abstractmethod
    async def update(self, product: Product) -> Product:
        pass

    @abstractmethod
    async def delete(self, product_id: int) -> bool:
        pass


class StockRepository(ABC):
    """Stock repository interface"""

    @abstractmethod
    async def get_by_product_id(self, product_id: int) -> Optional[Stock]:
        pass

    @abstractmethod
    async def create(self, stock: Stock) -> Stock:
        pass

    @abstractmethod
    async def update(self, stock: Stock) -> Stock:
        pass


class UserRepository(ABC):
    """User repository interface"""

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        pass

    @abstractmethod
    async def create(self, user: User) -> User:
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        pass


class CartRepository(ABC):
    """Cart repository interface"""

    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> Optional[Cart]:
        pass

    @abstractmethod
    async def create(self, cart: Cart) -> Cart:
        pass

    @abstractmethod
    async def update(self, cart: Cart) -> Cart:
        pass

    @abstractmethod
    async def delete(self, cart_id: int) -> bool:
        pass


class OrderRepository(ABC):
    """Order repository interface"""

    @abstractmethod
    async def get_by_id(self, order_id: int) -> Optional[Order]:
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> List[Order]:
        pass

    @abstractmethod
    async def create(self, order: Order) -> Order:
        pass

    @abstractmethod
    async def update(self, order: Order) -> Order:
        pass
