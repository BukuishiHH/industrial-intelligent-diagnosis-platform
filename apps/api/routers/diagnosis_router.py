# -*- coding: utf-8 -*-
"""设备检修诊断接口（BG-01）。

流程：POST /diagnosis/query 发起 -> 可能返回澄清或待审核 -> POST /diagnosis/review 恢复 -> GET /diagnosis/report 取报告。
"""
from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends

from dependencies import get_current_user_id
from packages.core.Result.Result import Result
from packages.core.Result.ResultCode import ResultCode
from packages.service.diagnosis_service import DiagnosisService
from packages.service.schemas import DiagnosisOut, DiagnosisQueryIn, ReviewIn

diagnosis_router = APIRouter(prefix="/diagnosis", tags=["设备检修诊断"])

_service: DiagnosisService | None = None


def get_service() -> DiagnosisService:
    """进程内单例（含 LangGraph MemorySaver，用于中断恢复）。"""
    global _service
    if _service is None:
        _service = DiagnosisService(
            data_path=os.getenv("SENSOR_DATA_PATH"),
            use_llm=os.getenv("DIAGNOSIS_USE_LLM", "1") != "0",
        )
    return _service


def _to_out(out: dict[str, Any]) -> DiagnosisOut:
    return DiagnosisOut(**out)


@diagnosis_router.post("/query", response_model=Result[DiagnosisOut], summary="发起设备诊断")
def start_diagnosis(body: DiagnosisQueryIn, user_id: int = Depends(get_current_user_id)):
    out = get_service().start(body.query, user_id=user_id, session_id=body.session_id)
    return Result.success(_to_out(out))


@diagnosis_router.post("/review", response_model=Result[DiagnosisOut], summary="澄清回答 / 人工审核")
def review(body: ReviewIn, user_id: int = Depends(get_current_user_id)):
    answer: dict[str, Any] = {"user_id": user_id}
    if body.device_id:
        answer["device_id"] = body.device_id
    if body.decision:
        answer["decision"] = body.decision
    if body.comment:
        answer["comment"] = body.comment
    if len(answer) == 1:
        return Result.error_msg(ResultCode.BAD_REQUEST, "请至少提供 device_id 或 decision")
    try:
        # user_id 同时用于归属校验：只有会话发起人本人能继续澄清/审核
        out = get_service().resume(body.thread_id, answer, user_id=user_id)
    except PermissionError as exc:
        return Result.error_msg(ResultCode.FORBIDDEN, str(exc))
    return Result.success(_to_out(out))


@diagnosis_router.get("/report/{report_id}", response_model=Result[dict], summary="获取诊断报告（Markdown）")
def get_report(report_id: str, user_id: int = Depends(get_current_user_id)):
    service = get_service()
    # 只允许读取本人发起的诊断报告；他人的报告与不存在的报告返回同样的 404
    markdown = service.report(report_id, user_id)
    if markdown is None:
        return Result.error_msg(ResultCode.NOT_FOUND, "报告不存在")
    return Result.success({"report_id": report_id, "format": "markdown",
                           "content": markdown, "record": service.record(report_id, user_id)})


@diagnosis_router.get("/history", response_model=Result[list[dict]], summary="历史诊断报告")
def history(limit: int = 20, user_id: int = Depends(get_current_user_id)):
    # 历史按用户隔离：只返回当前登录用户发起的诊断
    return Result.success(get_service().history(limit, user_id))


@diagnosis_router.get("/state/{thread_id}", response_model=Result[dict], summary="查看诊断会话状态")
def state(thread_id: str, user_id: int = Depends(get_current_user_id)):
    try:
        return Result.success(get_service().state_of(thread_id, user_id))
    except PermissionError as exc:
        return Result.error_msg(ResultCode.FORBIDDEN, str(exc))
