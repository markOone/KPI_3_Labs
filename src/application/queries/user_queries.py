from pydantic import BaseModel, ConfigDict


class GetUserQuery(BaseModel):
    # """Query to get a user by ID"""
    model_config = ConfigDict(frozen=True)
    user_id: int
