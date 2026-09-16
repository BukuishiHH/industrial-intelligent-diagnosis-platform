from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from packages.core.Result.ResultCode import ResultCode
from packages.core.errors import BusinessException
from packages.core.Result.Result import Result


# HTTP 状态码 -> 业务码 映射
_HTTP_STATUS_TO_RESULT_CODE: dict[int, ResultCode] = {
    400: ResultCode.BAD_REQUEST,
    401: ResultCode.UNAUTHORIZED,
    403: ResultCode.FORBIDDEN,
    404: ResultCode.NOT_FOUND,
    409: ResultCode.CONFLICT,
    500: ResultCode.SERVER_ERROR,
    501: ResultCode.BUSINESS_FAIL,
}


def _http_status_for(result_code: ResultCode) -> int:
    """ 业务码即 HTTP 状态码；非法值退化为 500, 避免构造出无效 HTTP 响应 """
    code = result_code.get_code
    return code if 100 <= code <= 599 else 500


def _json_response(result: Result, status_code: int) -> JSONResponse:
    """ 统一出口：业务码与 HTTP 状态码保持一致
    JSONResponse 不经过 FastAPI 的 jsonable_encoder, 故必须用 mode="json"
    否则 data 中的 datetime/Decimal/Enum/嵌套模型会触发序列化异常 """
    return JSONResponse(
        status_code=status_code,
        content=result.model_dump(mode="json"),
    )


def _summarize_validation_errors(errors: list) -> str:
    """ 将 pydantic 校验错误压平成可读文本
    只取 loc/msg, 避开 ctx 中不可序列化的对象(如 ValueError 实例) """
    parts = []
    for error in errors:
        loc = ".".join(str(item) for item in error.get("loc", ()))
        msg = str(error.get("msg", ""))
        parts.append(f"{loc}: {msg}" if loc else msg)
    return "; ".join(part for part in parts if part) or ResultCode.BAD_REQUEST.get_message


async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    """ 全局业务异常处理器：统一转换为 Result 响应 """
    return _json_response(
        Result.error_msg(exc.result_code, message=exc.message),
        _http_status_for(exc.result_code),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """ 参数校验失败处理器：按 §6.2 归并为 400
    有意替换 FastAPI 原生的 422 与 {"detail": [...]} 结构 """
    return _json_response(
        Result.error_msg(ResultCode.BAD_REQUEST, message=_summarize_validation_errors(exc.errors())),
        _http_status_for(ResultCode.BAD_REQUEST),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """ HTTP 异常处理器(含路由 404、HTTPBearer 鉴权失败等)：纳入统一响应格式
    枚举内状态码使用项目文案; 枚举外状态码(如 405/429)沿用原状态码与框架 detail """
    result_code = _HTTP_STATUS_TO_RESULT_CODE.get(exc.status_code)
    if result_code is not None:
        return _json_response(Result.error(result_code), _http_status_for(result_code))
    message = exc.detail if isinstance(exc.detail, str) and exc.detail else "请求处理失败"
    return _json_response(
        Result(code=exc.status_code, message=message, data=None),
        exc.status_code,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """ 全局兜底异常处理器：未知异常统一返回内部错误 """
    return _json_response(
        Result.error_msg(ResultCode.SERVER_ERROR, message="服务器内部错误"),
        _http_status_for(ResultCode.SERVER_ERROR),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """ 向 FastAPI 应用注册全局异常处理器(需在创建 app 后调用, 见 apps/api/main.py) """
    app.add_exception_handler(BusinessException, business_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
