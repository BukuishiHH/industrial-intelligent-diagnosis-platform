from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from packages.core.database import get_db
from packages.user.schemas import RegisterRequest,LoginRequest,TokenResponse,UserOut
from packages.user.service import user_service
from packages.core.Result.Result import Result


# 路由实例
user_router = APIRouter(
    prefix = "/user",
    tags = ["用户登录/注册"],
)


# 注册接口
@user_router.post(
    "/register",
    response_model=Result[UserOut],
    summary="用户注册",)
def register(
    reg: RegisterRequest,
    db: Session = Depends(get_db),
    ):
    return Result.success(user_service.user_register(reg, db))


# 登录接口
@user_router.post(
    "/login",
    response_model=Result[TokenResponse],
    summary="用户登录",)
def login(
    log: LoginRequest,
    db: Session = Depends(get_db),
    ):
    return Result.success(user_service.user_login(log, db))