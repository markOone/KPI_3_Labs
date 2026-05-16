from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from src.domain.value_objects.value_objects import Email, Money, Quantity, Sku


@dataclass
class Product:
    """Domain Product entity"""
    id: int
    name: str
    sku: Sku
    price: Money
    category_id: int

    def validate(self):
        """Validate product invariants"""
        if not self.name or len(self.name) == 0:
            raise ValueError("Product name cannot be empty")
        if self.price.amount <= 0:
            raise ValueError("Product price must be positive")


@dataclass
class Stock:
    """Domain Stock entity"""
    id: int
    product_id: int
    quantity: Quantity

    def reduce(self, qty: Quantity) -> None:
        """Reduce stock by quantity"""
        self.quantity = self.quantity - qty

    def increase(self, qty: Quantity) -> None:
        """Increase stock by quantity"""
        self.quantity = self.quantity + qty

    def has_enough(self, qty: Quantity) -> bool:
        """Check if there's enough stock"""
        return self.quantity.value >= qty.value


@dataclass
class User:
    """Domain User entity"""
    id: int
    email: Email
    username: str
    password_hash: str
    group_id: Optional[int] = None

    def validate(self):
        """Validate user invariants"""
        if not self.username or len(self.username) == 0:
            raise ValueError("Username cannot be empty")


@dataclass
class CartItem:
    """Domain CartItem entity"""
    id: int
    product_id: int
    quantity: Quantity
    price: Money

    def total_price(self) -> Money:
        return self.price * self.quantity.value


@dataclass
class Cart:
    """Domain Cart aggregate root"""
    id: int
    user_id: int
    items: List[CartItem]

    def add_item(self, product_id: int, quantity: Quantity, price: Money) -> None:
        """Add or update item in cart"""
        for item in self.items:
            if item.product_id == product_id:
                item.quantity = item.quantity + quantity
                return
        self.items.append(CartItem(id=0, product_id=product_id, quantity=quantity, price=price))

    def remove_item(self, product_id: int) -> None:
        """Remove item from cart"""
        self.items = [item for item in self.items if item.product_id != product_id]

    def clear(self) -> None:
        """Clear all items from cart"""
        self.items = []

    def total_price(self) -> Money:
        """Calculate total cart price"""
        total = Money(0)
        for item in self.items:
            total = total + item.total_price()
        return total


@dataclass
class OrderItem:
    """Domain OrderItem entity"""
    id: int
    product_id: int
    quantity: Quantity
    price_at_purchase: Money

    def total_price(self) -> Money:
        return self.price_at_purchase * self.quantity.value


@dataclass
class Order:
    """Domain Order aggregate root"""
    id: int
    user_id: int
    items: List[OrderItem]
    status: str
    total_price: Money
    created_at: datetime

    def can_cancel(self) -> bool:
        """Check if order can be cancelled"""
        return self.status == "pending"

    def validate(self):
        """Validate order invariants"""
        if not self.items or len(self.items) == 0:
            raise ValueError("Order must have at least one item")
        if self.status not in ["pending", "confirmed", "shipped", "delivered", "cancelled"]:
            raise ValueError(f"Invalid order status: {self.status}")
