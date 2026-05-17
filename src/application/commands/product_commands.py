from typing import Optional
from pydantic import BaseModel, ConfigDict

class CreateProductCommand(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    sku: str
    price: float
    category_id: int

class UpdateProductCommand(BaseModel):
    model_config = ConfigDict(frozen=True)
    product_id: int
    name: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[float] = None
    category_id: Optional[int] = None

class DeleteProductCommand(BaseModel):
    model_config = ConfigDict(frozen=True)
    product_id: int