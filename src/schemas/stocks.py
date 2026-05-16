from pydantic import BaseModel, Field

class StockUpdate(BaseModel):
    quantity: int = Field(..., ge=0, description="Нова кількість товару")