from typing import Generic, Optional, TypeVar
from pydantic import BaseModel, Field

from .ResultCode import ResultCode


T = TypeVar("T")


class Result(BaseModel, Generic[T]):
    """
    统一API响应结果封装
    """
    code: int = Field(description="响应状态码")
    message: str = Field(description="响应消息")
    trace_id: Optional[str] = Field(default = None, description = "响应追踪ID")
    data: Optional[T] = Field(default=None, description="响应泛型数据")

    @classmethod
    def success(cls, data: T) -> "Result[T]":
        """成功, 使用默认消息"""
        return cls(
            code=ResultCode.SUCCESS.get_code,
            message=ResultCode.SUCCESS.get_message,
            data=data
        )

    @classmethod
    def success_msg(cls, message: str, data: T) -> "Result[T]":
        """成功, 自定义message"""
        return cls(
            code=ResultCode.SUCCESS.get_code,
            message=message,
            data=data
        )

    @classmethod
    def error(cls, result_code: ResultCode) -> "Result[T]":
        """失败: 传入枚举, data=None"""
        return cls(
            code=result_code.get_code,
            message=result_code.get_message,
            data=None
        )

    @classmethod
    def error_msg(cls, result_code: ResultCode, message: str) -> "Result[T]":
        """失败: 枚举 + 自定义消息, data=None"""
        return cls(
            code=result_code.get_code,
            message=message,
            data=None
        )

    @classmethod
    def error_with_data(cls, result_code: ResultCode, message: str, data: T) -> "Result[T]":
        """失败: 枚举 + 自定义消息 + 携带返回数据"""
        return cls(
            code=result_code.get_code,
            message=message,
            data=data
        )