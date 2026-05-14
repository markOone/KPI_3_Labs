from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal

class CartItemAdd(BaseModel):
    product_id: int = Field(..., description="ID товару")
    quantity: Decimal = Field(..., gt=0, description="Кількість товару (більше 0)")

class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: Decimal

    model_config = ConfigDict(from_attributes=True)