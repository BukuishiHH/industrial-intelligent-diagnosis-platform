from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session
from packages.core.database import get_db
from packages.core.security.jwt_util import decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from packages.core.errors import InvalidTokenError


bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> int:
    """从 Authorization: Bearer <token> 解析出当前登录用户的 user_id"""
    if credentials is None:
        raise InvalidTokenError("缺少认证凭证，请登录")
    payload = decode_token(credentials.credentials)
    subject = payload.get("sub")
    if subject is None:
        raise InvalidTokenError("token 缺少 sub 声明")
    try:
        return int(subject)
    except (TypeError, ValueError):
        raise InvalidTokenError("token 的 sub 声明非法")
