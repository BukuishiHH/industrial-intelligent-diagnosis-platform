# JWT 工具：生成与解析 access token
import uuid
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from jwt.exceptions import ExpiredSignatureError
from jwt.exceptions import InvalidTokenError as JWTDecodeError
from packages.core.config import settings
from packages.core.errors import TokenExpiredError, InvalidTokenError


# 生成 Token
def create_access_token(
    user_id: str,
    username: str = "",
    expires_days: Optional[int] = None,
) -> str:
    """
    生成 access token。
    :param user_id: 用户业务 ID(字符串)
    :param username: 用户名
    :param expires_days: 过期天数，默认取 settings.JWT_EXPIRE_DAYS
    :return: JWT 字符串
    """
    days = expires_days if expires_days is not None else settings.JWT_EXPIRE_DAYS
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),                    # 用户 ID
        "username": username,                   # 用户名
        "type": "access",                       # token 类型，预留 refresh
        "jti": uuid.uuid4().hex,                # token 唯一 ID，便于吊销
        "iat": int(now.timestamp()),            # 签发时间
        "exp": int((now + timedelta(days=days)).timestamp()),  # 过期时间
    }
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


# 解析 Token
def decode_token(token: str) -> dict:
    """
    解析并校验 token。
    :param token: JWT 字符串
    :return: payload dict
    :raises TokenExpiredError: token 已过期
    :raises InvalidTokenError: token 无效
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],   # 显式指定，防算法混淆攻击
        )
        return payload
    except ExpiredSignatureError:
        raise TokenExpiredError("token 已过期")
    except JWTDecodeError as e:
        raise InvalidTokenError(f"token 无效: {e}")