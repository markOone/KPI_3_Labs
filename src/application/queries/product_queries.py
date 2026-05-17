from pydantic import BaseModel, ConfigDict

class GetProductQuery(BaseModel):
    model_config = ConfigDict(frozen=True)
    product_id: int

class GetAllProductsQuery(BaseModel):
    model_config = ConfigDict(frozen=True)
    skip: int = 0
    limit: int = 100