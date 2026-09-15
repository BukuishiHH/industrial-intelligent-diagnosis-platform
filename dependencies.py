from fastapi import Depends
from sqlalchemy.orm import Session
from packages.core.database import get_db
from packages.core.security.jwt_util import decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


bearer_scheme = HTTPBearer()

def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> int:
    """从 Authorization: Bearer <token> 解析出当前登录用户的 user_id"""
    payload = decode_token(credentials.credentials)
    return int(payload["sub"])
