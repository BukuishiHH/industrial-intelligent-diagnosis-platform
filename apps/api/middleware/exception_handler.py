from typing import Optional, Union

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from packages.core.Result.ResultCode import ResultCode
from packages.core.errors import BusinessException
from packages.core.Result.Result import Result


async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    """ 全局业务异常处理器：统一转换为 Result 响应 """
    return JSONResponse(
        status_code=200,  # 业务码随响应体返回，HTTP 层统一 200
        content=Result.error(ResultCode(exc.code), msg=exc.message).model_dump(),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """ 全局兜底异常处理器：未知异常统一返回内部错误 """
    return JSONResponse(
        status_code=500,
        content=Result.error_msg(
            ResultCode.SERVER_ERROR,
            msg="服务器内部错误",
        ).model_dump(),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """ 向 FastAPI 应用注册全局异常处理器 """
    app.add_exception_handler(BusinessException, business_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)