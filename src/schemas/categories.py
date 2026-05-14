from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Назва категорії")

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)

class CategoryResponse(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)