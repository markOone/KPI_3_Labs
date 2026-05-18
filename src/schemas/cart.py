from pydantic import BaseModel


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
