from pydantic import BaseModel, ConfigDict


class AddUserCommand(BaseModel):
    # """Command to add a new user"""
    model_config = ConfigDict(frozen=True)

    email: str
    username: str
    password: str


class LoginUserCommand(BaseModel):
    # """Command to log in a user"""
    model_config = ConfigDict(frozen=True)

    username: str
    password: str
