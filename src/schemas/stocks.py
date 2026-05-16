from pydantic import BaseModel, Field
from decimal import Decimal


class StockUpdate(BaseModel):
    # ge=0 гарантує, що адмін не введе від'ємне число
    quantity: int = Field(..., ge=0, description="Нова кількість товару")
