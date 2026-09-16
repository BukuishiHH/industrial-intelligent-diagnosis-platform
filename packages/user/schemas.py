from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=12, description="用户名称")
    password: str = Field(..., min_length=6, max_length=16, description="用户密码")
    pwd_confirm: str = Field(..., min_length=6, max_length=16, description="第二次输入的密码")


class LoginRequest(BaseModel):
    username: str = Field(..., description="用户名称")
    password: str = Field(..., description="用户密码")


class UserOut(BaseModel):
    id: int
    username: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"