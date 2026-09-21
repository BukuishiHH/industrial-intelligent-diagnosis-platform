# -*- coding: utf-8 -*-
"""诊断链路的结构化数据契约。

对应设计文档《业务场景设计_设备检修诊断》§7：
A4 → A1 必须结构化；A1 只做装配，不二次生成；A5 从 state 取字段填报告模板。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

Intent = Literal["equipment_diagnosis", "other"]
TimeExprType = Literal["range", "point", "none"]
CauseCode = Literal[
    "ROTOR_UNBALANCE", "RUB_IMPACT", "COUPLING_DAMAGE", "BEARING_DAMAGE",
    "BEARING_TEMP_HIGH", "LUBRICATION_FAULT", "ELECTRICAL_FAULT",
    "SURGE", "BASE_LOOSENESS", "UNKNOWN",
]
Urgency = Literal["立即停机", "紧急停机", "计划停机", "运行观察"]


# ---------------- A1 意图与槽位 ----------------
class TimeExpression(BaseModel):
    type: TimeExprType = "none"
    start: datetime | None = None
    end: datetime | None = None
    center: datetime | None = None
    raw_text: str | None = None


class IntentResult(BaseModel):
    intent: Intent = "equipment_diagnosis"
    device_id: str | None = None
    time_expression: TimeExpression = Field(default_factory=TimeExpression)
    sensor_hint: list[str] = Field(default_factory=list)
    symptom: str | None = None
    missing_slots: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    raw_query: str = ""


# ---------------- A2 检索 ----------------
class RetrievedChunk(BaseModel):
    chunk_id: str
    text: str
    score: float = 0.0
    rerank_score: float | None = None
    doc_id: str | None = None
    doc_type: str | None = None
    device_id: str | None = None
    section: str | None = None
    page: int | None = None
    case_no: str | None = None
    locator: str | None = None


# ---------------- A3 数据检索 ----------------
class SensorStats(BaseModel):
    sensor: str
    unit: str = ""
    count: int = 0
    first: float | None = None
    last: float | None = None
    mean: float | None = None
    max: float | None = None
    min: float | None = None
    rms: float | None = None
    std: float | None = None
    peak_to_peak: float | None = None
    trend_slope_per_hour: float | None = None
    change_over_window: float | None = None
    max_delta_10min: float | None = None
    status: Literal["normal", "warning", "alarm", "trip", "unknown"] = "unknown"
    over_alarm_count: int = 0
    first_over_alarm_time: datetime | None = None
    over_trip_count: int = 0


class ThresholdHit(BaseModel):
    sensor: str
    level: Literal["warning", "alarm", "trip"]
    value: float
    limit: float
    at: datetime | None = None
    description: str = ""


class TrendHit(BaseModel):
    rule_id: str
    sensor: str
    value: float
    threshold: float
    unit: str = ""
    conclusion: str = ""
    case_hint: str | None = None
    detail: str = ""


class DataQuality(BaseModel):
    points: int = 0
    expected_points: int | None = None
    interval_seconds: int = 60
    requested_hours: float | None = None
    covered_hours: float | None = None
    coverage: float | None = None
    missing_rate: float | None = None
    warnings: list[str] = Field(default_factory=list)


class SensorDigest(BaseModel):
    """A3 输出：统计特征 + 阈值/趋势判定 + 数据可用性（原始序列不进 prompt）。"""

    digest_id: str = ""
    device_id: str = ""
    device_model: str | None = None
    start: datetime | None = None
    end: datetime | None = None
    sensors: list[SensorStats] = Field(default_factory=list)
    threshold_hits: list[ThresholdHit] = Field(default_factory=list)
    trend_hits: list[TrendHit] = Field(default_factory=list)
    data_quality: DataQuality = Field(default_factory=DataQuality)
    series: dict[str, list[float]] = Field(default_factory=dict)   # 降采样序列，仅供前端画图
    series_timestamps: list[str] = Field(default_factory=list)
    summary_lines: list[str] = Field(default_factory=list)          # 给 A1/A4 的紧凑文本
    empty: bool = False


# ---------------- A4 诊断结论 ----------------
class Evidence(BaseModel):
    source: Literal["manual", "sensor"]
    ref: str
    statement: str


class CandidateCause(BaseModel):
    code: CauseCode = "UNKNOWN"
    name: str
    confidence: float = 0.0
    evidence: list[Evidence] = Field(default_factory=list)


class RootCause(BaseModel):
    code: CauseCode = "UNKNOWN"
    name: str
    confidence: float = 0.0
    basis: str = ""


class SolutionStep(BaseModel):
    no: int
    action: str
    ref: str | None = None


class Solution(BaseModel):
    urgency: Urgency = "运行观察"
    steps: list[SolutionStep] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)


class DiagnosisResult(BaseModel):
    diagnosis_id: str = ""
    device_id: str = ""
    device_model: str | None = None
    start: datetime | None = None
    end: datetime | None = None
    symptoms: list[str] = Field(default_factory=list)
    candidate_causes: list[CandidateCause] = Field(default_factory=list)
    root_cause: RootCause | None = None
    solution: Solution = Field(default_factory=Solution)
    data_quality: DataQuality = Field(default_factory=DataQuality)
    threshold_hits: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    need_more_info: bool = False
    overall_confidence: float = 0.0
    references: dict[str, Any] = Field(default_factory=dict)
    model: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


# ---------------- HITL 与展示 ----------------
class HitlDecision(BaseModel):
    decision: Literal["confirm", "reject"] = "confirm"
    reviewer_user_id: int | None = None
    decided_at: datetime | None = None
    reason_category: str | None = None
    comment: str | None = None


class CardAction(BaseModel):
    key: str
    label: str
    enabled: bool = True


class EvidenceItem(BaseModel):
    text: str
    locator: str | None = None
    chart_ref: str | None = None


class EvidenceGroup(BaseModel):
    source: Literal["manual", "sensor"]
    items: list[EvidenceItem] = Field(default_factory=list)


class DiagnosisCard(BaseModel):
    """A1 → 前端：除 summary 外，其余字段逐字段取自 state。"""

    type: Literal["diagnosis_card", "clarification_card", "message"] = "diagnosis_card"
    summary: str = ""
    window_note: str = ""
    urgency: str = ""                       # 处置紧迫度（运行观察/计划停机/紧急停机）
    overall_confidence: float = 0.0
    root_cause: dict[str, Any] = Field(default_factory=dict)
    evidence_groups: list[EvidenceGroup] = Field(default_factory=list)
    solution_steps: list[str] = Field(default_factory=list)
    candidate_alternatives: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[CardAction] = Field(default_factory=list)
    diagnosis_id: str = ""
    degraded: bool = False
    notes: list[str] = Field(default_factory=list)
    options: list[dict[str, Any]] = Field(default_factory=list)     # 澄清卡片用
