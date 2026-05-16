from pydantic import BaseModel, EmailStr


class UserRegisterSchema(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLoginSchema(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponseSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    username: str
    email: EmailStr
