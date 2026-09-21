# -*- coding: utf-8 -*-
"""诊断相关的 API 出入参模型。"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class DiagnosisQueryIn(BaseModel):
    query: str = Field(min_length=1, max_length=500, description="用户的自然语言提问")
    session_id: str | None = Field(default=None, description="会话 ID；留空则新建（用于澄清/审核的中断恢复）")


class ReviewIn(BaseModel):
    thread_id: str = Field(description="诊断会话 ID（由 /diagnosis/query 返回）")
    decision: Literal["confirm", "reject"] | None = Field(default=None, description="人工审核结论（本期仅实现 confirm）")
    device_id: str | None = Field(default=None, description="澄清回答：用户选择的设备位号")
    comment: str | None = Field(default=None, description="审核意见")


class DiagnosisOut(BaseModel):
    thread_id: str
    status: Literal["awaiting_clarification", "awaiting_review", "completed"]
    payload: dict[str, Any] | None = None
    diagnosis_id: str | None = None
    report_id: str | None = None
    report_markdown: str | None = None
    card: dict[str, Any] | None = None
    timings: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    search_trace: dict[str, Any] = Field(default_factory=dict)
