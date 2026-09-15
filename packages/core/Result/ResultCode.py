from enum import Enum


class ResultCode(Enum):
    """
    全局API响应状态码枚举
    """
    # 成功
    SUCCESS = (200, "操作成功")

    # 客户端错误 4xx
    BAD_REQUEST = (400, "请求参数错误")
    UNAUTHORIZED = (401, "未授权，请登录")
    FORBIDDEN = (403, "权限不足，拒绝访问")
    NOT_FOUND = (404, "资源不存在")

    # 服务端错误 5xx
    SERVER_ERROR = (500, "服务器内部异常")
    BUSINESS_FAIL = (501, "业务处理失败")

    def __init__(self, code: int, message: str):
        self._code = code
        self._message = message

    @property
    def get_code(self) -> int:
        return self._code

    @property
    def get_message(self) -> str:
        return self._message
