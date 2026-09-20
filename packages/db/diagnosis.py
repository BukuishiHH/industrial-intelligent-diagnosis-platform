# -*- coding: utf-8 -*-
"""诊断业务的数据库模型（MySQL，SQLAlchemy 2.0 风格，与 packages/db/user.py 一致）。

表结构对应设计文档《业务场景设计_设备检修诊断》§6 D2：
    diagnosis_record   诊断记录（一条诊断一行，含结构化结论字段）
    diagnosis_evidence 证据链（多条，可回溯到手册 locator / 测点时间窗）
    diagnosis_report   报告正文（Markdown，与诊断 1:1）
    hitl_review        人工审核记录（谁在何时确认/否定）
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from packages.core.database import Base


class DiagnosisRecord(Base):
    __tablename__ = "diagnosis_record"
    __table_args__ = (
        Index("idx_diag_device_created", "device_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    diagnosis_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True, comment="诊断编号")
    thread_id: Mapped[str | None] = mapped_column(String(64), index=True, comment="LangGraph 会话 ID（用于中断恢复）")
    user_id: Mapped[int | None] = mapped_column(BigInteger, index=True, comment="发起人用户 ID")
    query: Mapped[str | None] = mapped_column(String(500), comment="用户原始提问")
    intent: Mapped[str | None] = mapped_column(String(32), comment="意图：equipment_diagnosis/other")

    device_id: Mapped[str | None] = mapped_column(String(16), index=True, comment="设备位号")
    device_model: Mapped[str | None] = mapped_column(String(64), comment="设备型号")
    window_start: Mapped[datetime | None] = mapped_column(DateTime, comment="分析窗口起点")
    window_end: Mapped[datetime | None] = mapped_column(DateTime, comment="分析窗口终点")

    symptoms: Mapped[list | None] = mapped_column(JSON, comment="故障现象列表")
    root_cause_code: Mapped[str | None] = mapped_column(String(32), comment="根因编码")
    root_cause_name: Mapped[str | None] = mapped_column(String(128), comment="根因名称")
    root_cause_confidence: Mapped[float | None] = mapped_column(Float, comment="根因置信度")
    root_cause_basis: Mapped[str | None] = mapped_column(Text, comment="根因判定依据（排除逻辑）")
    urgency: Mapped[str | None] = mapped_column(String(16), comment="处置紧迫度")
    overall_confidence: Mapped[float | None] = mapped_column(Float, comment="总体置信度")
    need_more_info: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否信息不足")

    candidate_causes: Mapped[list | None] = mapped_column(JSON, comment="候选原因（含置信度）")
    solution: Mapped[dict | None] = mapped_column(JSON, comment="处置建议（步骤/安全提示）")
    threshold_hits: Mapped[list | None] = mapped_column(JSON, comment="阈值/趋势命中")
    evidence_gaps: Mapped[list | None] = mapped_column(JSON, comment="信息缺口")
    data_quality: Mapped[dict | None] = mapped_column(JSON, comment="数据可用性")
    references: Mapped[dict | None] = mapped_column(JSON, comment="引用清单（A2 chunks / A3 查询参数）")
    model_info: Mapped[dict | None] = mapped_column(JSON, comment="模型与提示词版本")

    status: Mapped[str] = mapped_column(String(16), default="PENDING_REVIEW", index=True,
                                        comment="状态：PENDING_REVIEW/CONFIRMED/REPORTED/REJECTED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now,
                                                 comment="更新时间")


class DiagnosisEvidence(Base):
    __tablename__ = "diagnosis_evidence"
    __table_args__ = (
        Index("idx_evidence_diag", "diagnosis_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    diagnosis_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="诊断编号")
    cause_code: Mapped[str | None] = mapped_column(String(32), comment="所属候选原因编码")
    cause_name: Mapped[str | None] = mapped_column(String(128), comment="所属候选原因名称")
    source: Mapped[str] = mapped_column(String(16), comment="证据来源：manual/sensor")
    ref: Mapped[str] = mapped_column(String(255), comment="溯源标识：手册 locator 或 测点@时间窗")
    statement: Mapped[str | None] = mapped_column(String(500), comment="证据说明")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class DiagnosisReport(Base):
    __tablename__ = "diagnosis_report"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    report_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True, comment="报告编号")
    diagnosis_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="诊断编号（1:1）")
    device_id: Mapped[str | None] = mapped_column(String(16), index=True)
    format: Mapped[str] = mapped_column(String(16), default="markdown", comment="报告格式")
    content: Mapped[str] = mapped_column(Text, comment="报告正文（Markdown）")
    chars: Mapped[int] = mapped_column(Integer, default=0, comment="正文字数")
    file_path: Mapped[str | None] = mapped_column(String(255), comment="本地文件副本路径（可选）")
    meta: Mapped[dict | None] = mapped_column(JSON, comment="生成元信息")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)


class HitlReview(Base):
    __tablename__ = "hitl_review"
    __table_args__ = (
        Index("idx_review_diag", "diagnosis_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    diagnosis_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="诊断编号")
    decision: Mapped[str] = mapped_column(String(16), comment="审核结论：confirm/reject")
    reviewer_user_id: Mapped[int | None] = mapped_column(BigInteger, index=True, comment="审核人用户 ID")
    reason_category: Mapped[str | None] = mapped_column(String(32), comment="否定原因分类（预留）")
    comment: Mapped[str | None] = mapped_column(String(500), comment="审核意见")
    decided_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="审核时间")
