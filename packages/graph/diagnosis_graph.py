# -*- coding: utf-8 -*-
"""BG-01 设备检修诊断的 LangGraph 单图编排。

图结构（设计文档 §4）：
    START -> a1(意图+槽位) --缺设备--> clarify(澄清, interrupt) --> dispatch
                           --其他意图--> END
                           --设备检修--> dispatch --> a2(知识检索) --\
                                                     --> a3(数据检索) ---> a4(推理)
    a4 -> review(人工审核, interrupt) --确认--> a5(报告+持久化) -> END
                                     --否定--> END(本期不实现，预留)

要点：
- a2 与 a3 并行 fan-out（无相互依赖），a4 隐式 join（两条入边都完成后执行）。
- HITL 用 interrupt/Command 实现，checkpointer 负责中断恢复。
- 结构化结论写进 state，A5 与持久化直接读 state（A1 只做呈现，不转发数据）。
"""
from __future__ import annotations

import operator
import time
from datetime import datetime
from typing import Annotated, Any, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from packages.agents.a1_intent import build_clarification_card, recognize
from packages.agents.a3_data import compute_digest
from packages.agents.a4_diagnosis import diagnose
from packages.agents.a5_report import generate_report
from packages.core.timewindow import TZ, resolve_window
from packages.rag.retriever import hybrid_search
from packages.schemas.diagnosis import (
    CardAction,
    DiagnosisCard,
    DiagnosisResult,
    EvidenceGroup,
    EvidenceItem,
    HitlDecision,
    IntentResult,
    RetrievedChunk,
    SensorDigest,
)


def _merge_dict(left: dict | None, right: dict | None) -> dict:
    return {**(left or {}), **(right or {})}


class DiagnosisState(TypedDict, total=False):
    # 输入
    query: str
    session_id: str
    thread_id: str          # LangGraph 会话 ID（随 state 传递，便于落库与审计）
    user_id: int
    data_path: str | None
    use_llm: bool
    # 中间产物
    intent: IntentResult
    window: dict
    digest: SensorDigest | None
    chunks: list[RetrievedChunk]
    search_trace: dict
    diagnosis: DiagnosisResult | None
    hitl: HitlDecision | None
    # 输出
    card: DiagnosisCard | None
    report_id: str | None
    report_markdown: str | None
    # a2 与 a3 并行执行，二者都可能产出提示信息：用 add 作为 reducer 累积，
    # 因此各节点只返回"本次新增"的条目，不要回传整份历史列表。
    errors: Annotated[list[str], operator.add]
    timings: Annotated[dict, _merge_dict]


def _tick(state: DiagnosisState, name: str, started: float) -> dict:
    timings = dict(state.get("timings") or {})
    timings[name] = round(time.time() - started, 2)
    return timings


# ---------------------------------------------------------------- 节点
def a1_node(state: DiagnosisState) -> dict:
    started = time.time()
    query = state.get("query", "")
    intent, channel = recognize(query, use_llm=state.get("use_llm", True))
    timings = _tick(state, "a1", started)
    new_errors = ["A1 走了规则回退通道（LLM 不可用）"] if channel == "rules" else []
    return {"intent": intent, "errors": new_errors, "timings": timings,
            "search_trace": {**(state.get("search_trace") or {}), "a1_channel": channel}}


def route_after_a1(state: DiagnosisState) -> str:
    intent = state.get("intent")
    if intent is None:
        return "end"
    if intent.intent != "equipment_diagnosis":
        return "end"
    if not intent.device_id:
        return "clarify"
    return "dispatch"


def clarify_node(state: DiagnosisState) -> dict:
    """缺设备位号 -> 强制澄清（决策 D2）。interrupt 返回用户选择。"""
    intent = state["intent"]
    card = build_clarification_card(intent)
    answer = interrupt({"type": "clarification_card", "card": card.model_dump(mode="json")})
    device_id = (answer or {}).get("device_id")
    new_intent = intent.model_copy(update={"device_id": device_id, "missing_slots": []})
    return {"intent": new_intent}


def dispatch_node(state: DiagnosisState) -> dict:
    """占位节点：把控制流分发到并行的 a2 / a3。"""
    return {}


def a3_node(state: DiagnosisState) -> dict:
    """数据检索：始终取该设备全部测点（诊断需要排除性证据）。"""
    started = time.time()
    intent = state["intent"]
    start, end, note, warns = resolve_window(intent.time_expression)
    digest = compute_digest(intent.device_id, start, end, sensors=None,
                            data_path=state.get("data_path"))
    return {"digest": digest,
            "window": {"start": start.isoformat(), "end": end.isoformat(), "note": note, "warnings": warns},
            "errors": list(warns or []), "timings": _tick(state, "a3", started)}


def a2_node(state: DiagnosisState) -> dict:
    started = time.time()
    intent = state["intent"]
    query = state["query"]
    parts = [query]
    if intent.symptom:
        parts.append(intent.symptom)
    new_errors: list[str] = []
    try:
        chunks, trace = hybrid_search("　".join(parts), device_id=intent.device_id, top_p=5)
    except Exception as exc:                      # noqa: BLE001
        # 检索完全失败也不终止会话：知识依据为空，A4 会相应下调置信度并标注缺证据
        from packages.rag.retriever import SearchTrace
        chunks, trace = [], SearchTrace(degraded=True, note=f"知识检索失败：{type(exc).__name__}")
        new_errors.append("知识检索失败，本次结论缺少手册依据")
    return {"chunks": chunks, "errors": new_errors,
            "search_trace": {**(state.get("search_trace") or {}),
                             "a2_steps": trace.steps, "a2_relaxed": trace.relaxed_to_global,
                             "a2_degraded": trace.degraded, "a2_note": trace.note},
            "timings": _tick(state, "a2", started)}


def a4_node(state: DiagnosisState) -> dict:
    started = time.time()
    intent, digest, chunks = state["intent"], state.get("digest"), state.get("chunks") or []
    trace: dict = {}
    try:
        result, trace = diagnose(state["query"], intent, digest, chunks, use_llm=state.get("use_llm", True))
    except Exception as exc:                       # noqa: BLE001
        # 推理失败不炸掉整个会话：降级为"信息不足"结论，并把失败原因暴露给用户
        from packages.schemas.diagnosis import DiagnosisResult as _DR
        result = _DR(device_id=intent.device_id,
                     start=digest.start if digest else None, end=digest.end if digest else None,
                     need_more_info=True, overall_confidence=0.0,
                     evidence_gaps=["诊断推理未能完成：" + f"{type(exc).__name__}: {str(exc)[:120]}"])
        trace = {"error": f"{type(exc).__name__}: {exc}"}
    result.diagnosis_id = f"dg_{datetime.now(TZ).strftime('%Y%m%d%H%M%S')}"

    # 结论一产出即落库（status=PENDING_REVIEW），形成"谁发起-结论-依据"的审计起点
    from packages.service.persistence import save_diagnosis
    saved = save_diagnosis(result, query=state.get("query"),
                           thread_id=state.get("thread_id") or state.get("session_id"),
                           user_id=state.get("user_id"))
    new_errors: list[str] = []
    if digest is not None and digest.empty:
        new_errors.append("A3 无数据：结论无实测依据")
    if not chunks:
        new_errors.append("A2 无检索结果：结论无手册依据")
    if not saved:
        new_errors.append("诊断记录入库失败（已保留本地文件副本）")
    return {"diagnosis": result, "errors": new_errors, "timings": _tick(state, "a4", started),
            "search_trace": {**(state.get("search_trace") or {}), "a4_prompt_chars": trace.get("prompt_chars"),
                             "a4_tokens": trace.get("tokens"),
                             "a4_validation": trace.get("validation_problems")}}


def _build_card(state: DiagnosisState) -> DiagnosisCard:
    """A1 侧的呈现装配：只有 summary 是生成的，其余字段逐字段取自 state。"""
    result = state.get("diagnosis")
    digest = state.get("digest")
    chunks = state.get("chunks") or []
    window = state.get("window") or {}
    if result is None:
        return DiagnosisCard(type="message", summary="未能形成诊断结论。")

    manual_items = [EvidenceItem(text=e.statement, locator=e.ref)
                    for c in result.candidate_causes for e in c.evidence if e.source == "manual"]
    sensor_items = [EvidenceItem(text=h) for h in result.threshold_hits]
    sensor_items += [EvidenceItem(text=e.statement, ref=None, locator=e.ref)
                     for c in result.candidate_causes for e in c.evidence if e.source == "sensor"]

    summary = ""
    if result.root_cause:
        summary = (f"{result.device_id} 最可能为{result.root_cause.name}"
                   f"（置信度 {result.root_cause.confidence:.2f}），建议{result.solution.urgency}。")
    else:
        summary = f"{result.device_id} 未形成明确根因，需补充证据。"

    return DiagnosisCard(
        type="diagnosis_card",
        summary=summary,
        window_note=window.get("note", ""),
        urgency=result.solution.urgency,
        overall_confidence=result.overall_confidence,
        root_cause={"name": result.root_cause.name if result.root_cause else None,
                    "confidence": result.root_cause.confidence if result.root_cause else None,
                    "basis": result.root_cause.basis if result.root_cause else None},
        evidence_groups=[EvidenceGroup(source="manual", items=manual_items[:6]),
                         EvidenceGroup(source="sensor", items=sensor_items[:8])],
        solution_steps=[f"{s.no}. {s.action}" for s in result.solution.steps],
        candidate_alternatives=[{"name": c.name, "confidence": c.confidence}
                                for c in result.candidate_causes
                                if not result.root_cause or c.name != result.root_cause.name],
        actions=[CardAction(key="confirm", label="确认", enabled=True),
                 CardAction(key="reject", label="否定", enabled=False)],
        diagnosis_id=result.diagnosis_id,
        degraded=bool(state.get("errors")),
        notes=list(state.get("errors") or []),
    )


def review_node(state: DiagnosisState) -> dict:
    card = _build_card(state)
    payload = {
        "type": "diagnosis_card",
        "card": card.model_dump(mode="json"),
        "diagnosis_id": (state.get("diagnosis").diagnosis_id if state.get("diagnosis") else None),
    }
    answer = interrupt(payload) or {}
    decision = HitlDecision(
        decision=answer.get("decision", "confirm"),
        reviewer_user_id=answer.get("user_id", state.get("user_id")),
        decided_at=datetime.now(TZ),
        comment=answer.get("comment"),
    )
    from packages.service.persistence import save_review
    if state.get("diagnosis"):
        save_review(state["diagnosis"].diagnosis_id, decision)
    return {"card": card, "hitl": decision}


def route_after_review(state: DiagnosisState) -> str:
    hitl = state.get("hitl")
    return "a5" if (hitl and hitl.decision == "confirm") else "end"


def a5_node(state: DiagnosisState) -> dict:
    started = time.time()
    result = state["diagnosis"]
    markdown, meta = generate_report(result, state.get("digest"), state.get("chunks"), state.get("hitl"))
    from packages.service.persistence import save_report
    report_id = save_report(result, markdown, state.get("hitl"), meta,
                            user_id=state.get("user_id"))
    return {"report_id": report_id, "report_markdown": markdown,
            "timings": _tick(state, "a5", started)}


# ---------------------------------------------------------------- 组图
def build_graph(checkpointer: Any | None = None):
    g = StateGraph(DiagnosisState)
    g.add_node("a1", a1_node)
    g.add_node("clarify", clarify_node)
    g.add_node("dispatch", dispatch_node)
    g.add_node("a2", a2_node)
    g.add_node("a3", a3_node)
    g.add_node("a4", a4_node)
    g.add_node("review", review_node)
    g.add_node("a5", a5_node)

    g.add_edge(START, "a1")
    g.add_conditional_edges("a1", route_after_a1,
                            {"clarify": "clarify", "dispatch": "dispatch", "end": END})
    g.add_edge("clarify", "dispatch")
    g.add_edge("dispatch", "a2")      # fan-out：a2 与 a3 并行
    g.add_edge("dispatch", "a3")
    g.add_edge("a2", "a4")            # 隐式 join：两条入边都完成才执行 a4
    g.add_edge("a3", "a4")
    g.add_edge("a4", "review")
    g.add_conditional_edges("review", route_after_review, {"a5": "a5", "end": END})
    g.add_edge("a5", END)

    return g.compile(checkpointer=checkpointer or MemorySaver())
