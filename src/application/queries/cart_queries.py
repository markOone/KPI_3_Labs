from pydantic import BaseModel, ConfigDict


class GetCartQuery(BaseModel):
    #  """Query to get the cart for a user"""
    model_config = ConfigDict(frozen=True)

    user_id: int
