from packages.user.dao import user_dao
from sqlalchemy.orm import Session
from packages.user.schemas import RegisterRequest, LoginRequest
from packages.core.errors import RegisterError, LoginError
from packages.core.Result.Result import Result
from packages.core.security.password_util import hash_password, verify_password
from packages.core.security.jwt_util import create_access_token


class UserService:

    # 用户注册
    def user_register(self, reg: RegisterRequest, db: Session):
        # 校验两次密码是否一致
        if  reg.password != reg.pwd_confirm:
            raise RegisterError("两次密码输入不一致！")
        
        # 校验用户名是否存在
        username = user_dao.get_username(reg.username, db)
        if username:
            raise RegisterError("注册的用户名已存在！")
        
        # 创建用户
        hash_pwd = hash_password(reg.password)
        user = user_dao.create_user(reg.username, hash_pwd, db)
        return {
        "id": user.userid,
        "username": user.username,
    }
    

    # 用户登录
    def user_login(self, log: LoginRequest, db:Session):
        # 获取用户
        user = user_dao.get_username(log.username, db)
        # 校验用户名
        if not user:
            raise LoginError("用户名或密码错误！")
        
        # 校验密码
        if not verify_password(log.password, user.password):
            raise LoginError("用户名或密码错误！")
        
        # 发放 token JWT令牌
        token = create_access_token(user_id=str(user.userid), username=user.username)
        return {
            "access_token": token,
            "token_type": "bearer",
        }
        


# 创建单例对象
user_service = UserService()