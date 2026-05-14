from pydantic import BaseModel, Field, ConfigDict

class CartItemAdd(BaseModel):
    product_id: int = Field(..., description="ID товару")
    quantity: float = Field(..., gt=0, description="Кількість товару (більше 0)")

class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: float

    model_config = ConfigDict(from_attributes=True)