from typing import List, Tuple
from pydantic import BaseModel, ConfigDict

class ProcessCheckoutCommand(BaseModel):
    model_config = ConfigDict(frozen=True)
    user_id: int

class CreateOrderCommand(BaseModel):
    model_config = ConfigDict(frozen=True)
    user_id: int
    items: List[Tuple[int, int, float]]
    total_price: float
    cart_id: int

class CancelOrderCommand(BaseModel):
    model_config = ConfigDict(frozen=True)
    order_id: int