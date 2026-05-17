from pydantic import BaseModel
from typing import Optional

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponseSchema(BaseModel):
    model_config = {"from_attributes": True, "frozen": True}

    id: int
    username: str
    email: str
    group_id: Optional[int] = None