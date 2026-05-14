from pydantic import BaseModel, ConfigDict
from typing import List
from datetime import datetime

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: float
    price_at_purchase: float

    model_config = ConfigDict(from_attributes=True)

class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: str
    total_price: float
    created_at: datetime
    items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)