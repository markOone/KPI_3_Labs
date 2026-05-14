from pydantic import BaseModel
from typing import List
from datetime import datetime

class OrderItemOut(BaseModel):
    product_id: int
    quantity: float
    price_at_purchase: float

class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: str
    total_price: float
    created_at: datetime
    items: List[OrderItemOut]
    