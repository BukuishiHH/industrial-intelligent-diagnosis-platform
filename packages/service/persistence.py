# -*- coding: utf-8 -*-
"""诊断结果的持久化：MySQL 落库（主）+ 本地文件副本（兜底/交付）。

设计原则：
- **数据库故障绝不阻断诊断链路**：所有 DB 操作都 try/except，失败时记录到 last_error 并退回文件存储。
- 诊断记录在 A4 产出结论后立即落库（status=PENDING_REVIEW），审核后更新状态，A5 生成报告后置 REPORTED，
  形成完整审计链：谁发起、结论是什么、依据是什么、谁在何时确认、报告何时生成。
- 报告正文同时入库（便于检索统计）与落盘（便于离线交付/人工查阅）。

表结构见 packages/db/diagnosis.py。
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from packages.core.config import BASE_DIR
from packages.core.timewindow import TZ
from packages.schemas.diagnosis import DiagnosisResult, HitlDecision

REPORTS_DIR = BASE_DIR / "data" / "reports"
INDEX_PATH = REPORTS_DIR / "index.jsonl"

_last_error: str | None = None


def last_error() -> str | None:
    """最近一次数据库写入错误（供接口/日志暴露，便于排查）。"""
    return _last_error


def _set_error(exc: Exception) -> None:
    global _last_error
    _last_error = f"{type(exc).__name__}: {exc}"
    print("[persistence] 数据库操作失败，已退回文件存储：" + _last_error)


def _naive(dt: datetime | None) -> datetime | None:
    """MySQL DATETIME 无时区：统一转成本地时间后去掉 tzinfo。"""
    return dt.astimezone(TZ).replace(tzinfo=None) if dt else None


def _session():
    from packages.core.database import session_factory
    return session_factory()


def _ensure_dir() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------- 诊断记录
def save_diagnosis(result: DiagnosisResult, query: str | None = None,
                   thread_id: str | None = None, user_id: int | None = None) -> bool:
    """A4 产出结论后落库（记录 + 证据链）。返回是否写库成功。"""
    from packages.db.diagnosis import DiagnosisEvidence, DiagnosisRecord

    try:
        session = _session()
        try:
            exists = session.query(DiagnosisRecord).filter_by(diagnosis_id=result.diagnosis_id).first()
            if exists:
                return True
            session.add(DiagnosisRecord(
                diagnosis_id=result.diagnosis_id,
                thread_id=thread_id,
                user_id=user_id,
                query=(query or "")[:500] or None,
                intent="equipment_diagnosis",
                device_id=result.device_id,
                device_model=result.device_model,
                window_start=_naive(result.start),
                window_end=_naive(result.end),
                symptoms=result.symptoms,
                root_cause_code=result.root_cause.code if result.root_cause else None,
                root_cause_name=result.root_cause.name if result.root_cause else None,
                root_cause_confidence=result.root_cause.confidence if result.root_cause else None,
                root_cause_basis=result.root_cause.basis if result.root_cause else None,
                urgency=result.solution.urgency,
                overall_confidence=result.overall_confidence,
                need_more_info=result.need_more_info,
                candidate_causes=[c.model_dump(mode="json") for c in result.candidate_causes],
                solution=result.solution.model_dump(mode="json"),
                threshold_hits=result.threshold_hits,
                evidence_gaps=result.evidence_gaps,
                data_quality=result.data_quality.model_dump(mode="json") if result.data_quality else None,
                references=result.references,
                model_info=result.model,
                status="PENDING_REVIEW",
            ))
            for cause in result.candidate_causes:
                for ev in cause.evidence:
                    session.add(DiagnosisEvidence(
                        diagnosis_id=result.diagnosis_id,
                        cause_code=cause.code, cause_name=cause.name,
                        source=ev.source, ref=ev.ref[:255], statement=(ev.statement or "")[:500],
                    ))
            session.commit()
            return True
        finally:
            session.close()
    except Exception as exc:                      # noqa: BLE001
        _set_error(exc)
        return False


def save_review(diagnosis_id: str, hitl: HitlDecision) -> bool:
    """人工审核后落库：写审核记录并更新诊断状态。"""
    from packages.db.diagnosis import DiagnosisRecord, HitlReview

    try:
        session = _session()
        try:
            session.add(HitlReview(
                diagnosis_id=diagnosis_id,
                decision=hitl.decision,
                reviewer_user_id=hitl.reviewer_user_id,
                reason_category=hitl.reason_category,
                comment=(hitl.comment or "")[:500] or None,
                decided_at=_naive(hitl.decided_at) or datetime.now(),
            ))
            record = session.query(DiagnosisRecord).filter_by(diagnosis_id=diagnosis_id).first()
            if record:
                record.status = "CONFIRMED" if hitl.decision == "confirm" else "REJECTED"
            session.commit()
            return True
        finally:
            session.close()
    except Exception as exc:                      # noqa: BLE001
        _set_error(exc)
        return False


# ---------------------------------------------------------------- 报告
def save_report(result: DiagnosisResult, markdown: str, hitl: HitlDecision | None,
                meta: dict[str, Any] | None = None, user_id: int | None = None) -> str:
    """A5：报告正文入库 + 落盘副本，并更新诊断状态为 REPORTED。

    user_id 会写入文件副本元数据，供"数据库不可用时的文件读取"做归属校验（见 load_report）。
    """
    report_id = result.diagnosis_id or f"dg_{datetime.now(TZ).strftime('%Y%m%d%H%M%S')}"

    _ensure_dir()
    file_path = REPORTS_DIR / f"{report_id}.md"
    file_path.write_text(markdown, encoding="utf-8")
    record = {
        "report_id": report_id, "diagnosis_id": result.diagnosis_id, "device_id": result.device_id,
        "user_id": user_id,
        "root_cause": {"code": result.root_cause.code, "name": result.root_cause.name,
                       "confidence": result.root_cause.confidence} if result.root_cause else None,
        "created_at": datetime.now(TZ).isoformat(),
    }
    (REPORTS_DIR / f"{report_id}.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(INDEX_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    from packages.db.diagnosis import DiagnosisRecord, DiagnosisReport
    try:
        session = _session()
        try:
            row = session.query(DiagnosisReport).filter_by(report_id=report_id).first()
            if row is None:
                session.add(DiagnosisReport(
                    report_id=report_id, diagnosis_id=result.diagnosis_id,
                    device_id=result.device_id, format="markdown", content=markdown,
                    chars=len(markdown), file_path=str(file_path.relative_to(BASE_DIR)),
                    meta=meta or {},
                ))
            else:
                row.content, row.chars, row.meta = markdown, len(markdown), meta or {}
            diag = session.query(DiagnosisRecord).filter_by(diagnosis_id=result.diagnosis_id).first()
            if diag:
                diag.status = "REPORTED"
            session.commit()
        finally:
            session.close()
    except Exception as exc:                      # noqa: BLE001
        _set_error(exc)
    return report_id


# ---------------------------------------------------------------- 读取
def load_report(report_id: str, user_id: int | None = None) -> str | None:
    """取报告正文（数据库优先，文件兜底）。

    **归属校验**：只返回属于 user_id 的报告；user_id 为空或不匹配一律返回 None
    （调用方应转成 404，不暴露"该报告是否存在"）。
    """
    if user_id is None:
        return None
    try:
        from packages.db.diagnosis import DiagnosisRecord, DiagnosisReport
        session = _session()
        try:
            row = session.query(DiagnosisReport).filter_by(report_id=report_id).first()
            if row:
                record = session.query(DiagnosisRecord).filter_by(
                    diagnosis_id=row.diagnosis_id).first()
                if record is None or record.user_id != user_id:
                    return None
                return row.content or None
        finally:
            session.close()
    except Exception as exc:                      # noqa: BLE001
        _set_error(exc)
    # 文件兜底：同样校验归属（元数据里的 user_id）
    meta_path = REPORTS_DIR / f"{report_id}.json"
    if not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if meta.get("user_id") != user_id:
        return None
    path = REPORTS_DIR / f"{report_id}.md"
    return path.read_text(encoding="utf-8") if path.exists() else None


def load_record(report_id: str, user_id: int | None = None) -> dict[str, Any] | None:
    """取结构化记录（诊断记录 + 审核记录），并校验归属。"""
    if user_id is None:
        return None
    try:
        from packages.db.diagnosis import DiagnosisRecord, HitlReview
        session = _session()
        try:
            diag = session.query(DiagnosisRecord).filter_by(diagnosis_id=report_id).first()
            if diag and diag.user_id != user_id:
                return None
            if diag:
                reviews = session.query(HitlReview).filter_by(diagnosis_id=report_id).all()
                return {
                    "diagnosis_id": diag.diagnosis_id, "device_id": diag.device_id,
                    "device_model": diag.device_model, "status": diag.status,
                    "window": {"start": str(diag.window_start), "end": str(diag.window_end)},
                    "root_cause": {"code": diag.root_cause_code, "name": diag.root_cause_name,
                                   "confidence": diag.root_cause_confidence, "basis": diag.root_cause_basis},
                    "urgency": diag.urgency, "overall_confidence": diag.overall_confidence,
                    "candidate_causes": diag.candidate_causes, "solution": diag.solution,
                    "threshold_hits": diag.threshold_hits, "evidence_gaps": diag.evidence_gaps,
                    "data_quality": diag.data_quality, "references": diag.references,
                    "created_at": str(diag.created_at),
                    "reviews": [{"decision": r.decision, "reviewer_user_id": r.reviewer_user_id,
                                 "comment": r.comment, "decided_at": str(r.decided_at)} for r in reviews],
                    "source": "database",
                }
        finally:
            session.close()
    except Exception as exc:                      # noqa: BLE001
        _set_error(exc)
    path = REPORTS_DIR / f"{report_id}.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("user_id") != user_id:
            return None
        data["source"] = "file"
        return data
    return None


def _empty_history_row(entry: dict[str, Any], source: str) -> dict[str, Any]:
    """统一历史列表的字段结构，避免数据库/文件两种来源返回不一致导致前端踩坑。"""
    return {
        "report_id": entry.get("report_id"),
        "diagnosis_id": entry.get("diagnosis_id"),
        "device_id": entry.get("device_id"),
        "root_cause": entry.get("root_cause"),
        "chars": entry.get("chars"),
        "status": entry.get("status"),
        "created_at": entry.get("created_at"),
        "source": source,
    }


def list_reports(limit: int = 20, user_id: int | None = None) -> list[dict[str, Any]]:
    """历史报告列表：**按用户隔离**，只返回该用户发起的诊断。

    user_id 为空时返回空列表（安全默认：宁可查不到，也不能越权看到别人的记录）。
    """
    if user_id is None:
        return []
    try:
        from packages.db.diagnosis import DiagnosisRecord, DiagnosisReport
        session = _session()
        try:
            rows = (session.query(DiagnosisReport, DiagnosisRecord)
                    .join(DiagnosisRecord,
                          DiagnosisRecord.diagnosis_id == DiagnosisReport.diagnosis_id)
                    .filter(DiagnosisRecord.user_id == user_id)
                    .order_by(DiagnosisReport.created_at.desc()).limit(limit).all())
            return [_empty_history_row({
                "report_id": rep.report_id, "diagnosis_id": rep.diagnosis_id,
                "device_id": rep.device_id, "chars": rep.chars,
                "status": rec.status if rec else None,
                "root_cause": ({"code": rec.root_cause_code, "name": rec.root_cause_name,
                                "confidence": rec.root_cause_confidence} if rec else None),
                "created_at": str(rep.created_at),
            }, "database") for rep, rec in rows]
        finally:
            session.close()
    except Exception as exc:                      # noqa: BLE001
        _set_error(exc)
    if not INDEX_PATH.exists():
        return []
    rows = [json.loads(x) for x in INDEX_PATH.read_text(encoding="utf-8").splitlines() if x.strip()]
    owned = [x for x in rows if x.get("user_id") == user_id]
    return [_empty_history_row(x, "file") for x in owned[-limit:][::-1]]


def db_health() -> tuple[bool, str]:
    """数据库连通性自检（供 check_env 与接口健康检查使用）。"""
    try:
        from sqlalchemy import text
        session = _session()
        try:
            session.execute(text("SELECT 1"))
            from packages.db.diagnosis import DiagnosisRecord
            count = session.query(DiagnosisRecord).count()
            return True, f"OK（diagnosis_record 现有 {count} 行）"
        finally:
            session.close()
    except Exception as exc:                      # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"
