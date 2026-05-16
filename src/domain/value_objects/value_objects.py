from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class Email:
    """Email value object"""
    value: str

    def __post_init__(self):
        if not self.value or '@' not in self.value:
            raise ValueError("Invalid email format")


@dataclass(frozen=True)
class Money:
    """Money value object"""
    amount: float

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

    def __add__(self, other: 'Money') -> 'Money':
        if not isinstance(other, Money):
            raise TypeError("Can only add Money to Money")
        return Money(self.amount + other.amount)

    def __mul__(self, quantity: float) -> 'Money':
        return Money(self.amount * quantity)


@dataclass(frozen=True)
class Quantity:
    """Quantity value object"""
    value: float

    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Quantity cannot be negative")

    def __add__(self, other: 'Quantity') -> 'Quantity':
        if not isinstance(other, Quantity):
            raise TypeError("Can only add Quantity to Quantity")
        return Quantity(self.value + other.value)

    def __sub__(self, other: 'Quantity') -> 'Quantity':
        if not isinstance(other, Quantity):
            raise TypeError("Can only subtract Quantity from Quantity")
        result = self.value - other.value
        if result < 0:
            raise ValueError("Cannot have negative quantity")
        return Quantity(result)


@dataclass(frozen=True)
class Sku:
    """Product SKU value object"""
    value: str

    def __post_init__(self):
        if not self.value or len(self.value) == 0:
            raise ValueError("SKU cannot be empty")
