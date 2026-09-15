from typing import Optional
from packages.core.Result.ResultCode import ResultCode


class BusinessException(Exception):
    """ 业务异常基类：所有业务异常统一携带 CodeEnum 状态码 """

    def __init__(
        self,
        code: ResultCode,
        message: Optional[str] = None,
        detail: Optional[str] = None,
    ):
        self.code: int = code.value                     # 存 int，与 Result.code 对齐
        self.message: str = message or code.message     # 默认取枚举绑定的提示语
        self.detail: Optional[str] = detail             # 附加调试信息
        super().__init__(self.message)


class TokenExpiredError(BusinessException):
    """ Token过期 """
    def __init__(self, message: Optional[str] = None, detail: Optional[str] = None):
        super().__init__(ResultCode.UNAUTHORIZED, message = message, detail = detail)


class InvalidTokenError(BusinessException):
    """Token 无效或格式错误"""
    def __init__(self, message: Optional[str] = None, detail: Optional[str] = None):
        super().__init__(ResultCode.BAD_REQUEST, message = message, detail = detail)