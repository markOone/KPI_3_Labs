from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
