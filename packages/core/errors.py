from typing import Optional
from packages.core.Result.ResultCode import ResultCode


class BusinessException(Exception):
    """ 业务异常基类：所有业务异常统一携带 CodeEnum 状态码 """

    def __init__(
        self,
        result_code: ResultCode,
        message: Optional[str] = None,
        detail: Optional[str] = None,
    ):
        self.result_code = result_code
        self.code = result_code.get_code
        self.message = message or result_code.get_message
        self.detail = detail
        super().__init__(self.message)


class TokenExpiredError(BusinessException):
    """ Token过期 """
    def __init__(self, message: Optional[str] = None, detail: Optional[str] = None):
        super().__init__(ResultCode.UNAUTHORIZED, message = message, detail = detail)


class InvalidTokenError(BusinessException):
    """Token 无效或格式错误"""
    def __init__(self, message: Optional[str] = None, detail: Optional[str] = None):
        super().__init__(ResultCode.BAD_REQUEST, message = message, detail = detail)