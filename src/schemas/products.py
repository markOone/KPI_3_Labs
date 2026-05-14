from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Назва товару")
    price: float = Field(..., gt=0, description="Ціна товару (більше 0)")
    sku: str = Field(..., min_length=3, max_length=50, description="Унікальний артикул")
    category_id: int = Field(..., gt=0, description="ID категорії")

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    price: Optional[float] = Field(None, gt=0)
    sku: Optional[str] = Field(None, min_length=3, max_length=50)
    category_id: Optional[int] = Field(None, gt=0)

class ProductResponse(ProductBase):
    id: int

    model_config = ConfigDict(from_attributes=True)