# -*- coding: utf-8 -*-
"""诊断服务：把 LangGraph 图封装成 API 可用的调用（含澄清与人工审核的中断/恢复）。"""
from __future__ import annotations

import uuid
from typing import Any

from langgraph.types import Command

from packages.core.config import BASE_DIR
from packages.graph.diagnosis_graph import build_graph
from packages.service.persistence import load_record, load_report, list_reports

CHECKPOINT_DIR = BASE_DIR / "data" / "checkpoints"


def build_checkpointer():
    """返回 (checkpointer, backend)。

    checkpoint 落 SQLite 文件（data/checkpoints/langgraph.sqlite），**服务重启后仍可恢复**中断中的
    澄清/审核会话；若 SQLite checkpointer 不可用则退回进程内 MemorySaver（功能降级但不报错）。
    """
    import os
    if os.getenv("CHECKPOINT_BACKEND", "sqlite").lower() == "memory":
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver(), "memory"
    try:
        import sqlite3

        from langgraph.checkpoint.sqlite import SqliteSaver

        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(CHECKPOINT_DIR / "langgraph.sqlite"), check_same_thread=False)
        serde = None
        try:
            # 显式登记本项目 state 中用到的 Pydantic 类型，避免 langgraph 升级后拒绝反序列化
            from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

            serde = JsonPlusSerializer(allowed_msgpack_modules=[
                ("packages.schemas.diagnosis", name)
                for name in ("IntentResult", "TimeExpression", "SensorDigest", "SensorStats",
                             "RetrievedChunk", "DiagnosisResult", "DiagnosisCard", "HitlDecision",
                             "DataQuality", "TrendHit", "ThresholdHit")
            ])
        except Exception:                          # noqa: BLE001
            serde = None
        saver = SqliteSaver(conn, serde=serde) if serde else SqliteSaver(conn)
        saver.setup()
        return saver, "sqlite"
    except Exception as exc:                       # noqa: BLE001
        print("[checkpointer] SQLite 不可用，退回内存：" + f"{type(exc).__name__}: {exc}")
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver(), "memory"


class DiagnosisService:
    def __init__(self, data_path: str | None = None, use_llm: bool = True, checkpointer=None):
        self.data_path = data_path
        self.use_llm = use_llm
        if checkpointer is None:
            checkpointer, self.checkpoint_backend = build_checkpointer()
        else:
            self.checkpoint_backend = "custom"
        self.graph = build_graph(checkpointer)

    # ---------------------------------------------------------------- 内部
    def _config(self, thread_id: str) -> dict:
        return {"configurable": {"thread_id": thread_id}}

    def _interrupt_payload(self, result: dict) -> dict | None:
        interrupts = result.get("__interrupt__")
        if not interrupts:
            return None
        first = interrupts[0]
        return getattr(first, "value", None) or (first.get("value") if isinstance(first, dict) else None)

    def _outcome(self, thread_id: str, result: dict) -> dict:
        payload = self._interrupt_payload(result)
        timings = result.get("timings") or {}
        if payload:
            kind = payload.get("type")
            return {
                "thread_id": thread_id,
                "status": "awaiting_clarification" if kind == "clarification_card" else "awaiting_review",
                "payload": payload,
                "timings": timings,
                "errors": result.get("errors") or [],
            }
        return {
            "thread_id": thread_id,
            "status": "completed",
            "diagnosis_id": result.get("diagnosis") .diagnosis_id if result.get("diagnosis") else None,
            "report_id": result.get("report_id"),
            "report_markdown": result.get("report_markdown"),
            "card": (result.get("card").model_dump(mode="json") if result.get("card") else None),
            "timings": timings,
            "errors": result.get("errors") or [],
            "search_trace": result.get("search_trace") or {},
        }

    # ---------------------------------------------------------------- 对外
    def start(self, query: str, user_id: int | None = None, session_id: str | None = None) -> dict:
        thread_id = session_id or f"th_{uuid.uuid4().hex[:12]}"
        init = {"query": query, "user_id": user_id or 0,
                "session_id": thread_id, "thread_id": thread_id,
                "data_path": self.data_path, "use_llm": self.use_llm,
                "errors": [], "timings": {}}
        result = self.graph.invoke(init, self._config(thread_id))
        return self._outcome(thread_id, result)

    def _owner_of(self, thread_id: str) -> int | None:
        """读取会话归属（初始 state 里写入的 user_id）。"""
        try:
            snapshot = self.graph.get_state(self._config(thread_id))
        except Exception:                              # noqa: BLE001
            return None
        if snapshot is None:
            return None
        return (snapshot.values or {}).get("user_id")

    def _assert_owner(self, thread_id: str, user_id: int | None) -> None:
        """越权防护：只有会话发起人本人能继续澄清/审核/查看状态。

        不存在或无归属的会话一律按"无权访问"处理，避免泄露会话是否存在。
        """
        owner = self._owner_of(thread_id)
        if owner is None or user_id is None or int(owner) != int(user_id):
            raise PermissionError("会话不存在或无权访问该诊断会话")

    def resume(self, thread_id: str, answer: dict, user_id: int | None = None) -> dict:
        """answer 为澄清结果 {'device_id': 'FJ-01'} 或审核结果 {'decision': 'confirm'}。"""
        self._assert_owner(thread_id, user_id)
        payload = dict(answer)
        payload["user_id"] = user_id if user_id is not None else payload.get("user_id")
        result = self.graph.invoke(Command(resume=payload), self._config(thread_id))
        return self._outcome(thread_id, result)

    def state_of(self, thread_id: str, user_id: int | None = None) -> dict:
        self._assert_owner(thread_id, user_id)
        snapshot = self.graph.get_state(self._config(thread_id))
        return {"values": {k: v for k, v in (snapshot.values or {}).items()
                           if k in ("query", "intent", "window", "errors", "timings", "report_id")},
                "next": list(snapshot.next or [])}

    def report(self, report_id: str, user_id: int | None = None) -> str | None:
        return load_report(report_id, user_id)

    def record(self, report_id: str, user_id: int | None = None) -> dict | None:
        return load_record(report_id, user_id)

    def history(self, limit: int = 20, user_id: int | None = None) -> list[dict]:
        return list_reports(limit, user_id)
