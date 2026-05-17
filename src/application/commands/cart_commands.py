from pydantic import BaseModel, ConfigDict


class AddToCartCommand(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: int
    product_id: int
    quantity: int


class RemoveFromCartCommand(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: int
    product_id: int


class ClearCartCommand(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: int
