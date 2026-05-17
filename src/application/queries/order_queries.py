from pydantic import BaseModel, ConfigDict

class GetOrderQuery(BaseModel):
    model_config = ConfigDict(frozen=True)
    order_id: int

class GetUserOrdersQuery(BaseModel):
    model_config = ConfigDict(frozen=True)
    user_id: int