# -*- coding: utf-8 -*-
"""A1 意图识别与槽位抽取节点。

设计约束（设计文档 §3.2 修正①）：
- **一次 LLM 调用**同时产出 intent + slots（function calling / json_object），不拆成两次。
- LLM 只做语义归一化（把"昨天上午"变成中心时刻），**不做时间算术** —— 时间窗由 core.timewindow 计算。
- 缺 device_id -> 强制澄清（决策 D2）；缺时间 -> 不澄清，走默认窗口（D1）。
- LLM 不可用时退化为规则解析（设备位号/时间词/症状词）。
"""
from __future__ import annotations

import json
import re
from datetime import datetime

from packages.core import thresholds
from packages.core.timewindow import TZ, parse_time_expression
from packages.schemas.diagnosis import DiagnosisCard, CardAction, IntentResult, TimeExpression

SYSTEM_PROMPT = """你是工业设备故障诊断平台的入口节点，负责理解用户的提问。
设备库：FJ-01、FJ-02、FJ-03（均为离心引风机；用户可能说"1号机""3号风机""FJ-01"等）。
你的任务：判断意图并抽取槽位，只输出 JSON：
{
  "intent": "equipment_diagnosis" | "other",
  "device_id": "FJ-01" | null,
  "time_expression": {"type": "range|point|none", "start": "ISO8601|null", "end": "ISO8601|null", "center": "ISO8601|null", "raw_text": "原文时间词"},
  "sensor_hint": ["v1", "v3", "bearing_temp", "oil_pressure", "current", "speed"],
  "symptom": "故障现象的一句话概括",
  "confidence": 0.0~1.0
}
判定要求：
- 与设备运行、故障、检修、报警、参数异常相关的提问 -> equipment_diagnosis；闲聊、与设备无关 -> other。
- 时间表达不要自己换算成窗口，只给出语义：明确起止用 range；只说"昨天上午/3月5日8点"这种单点或模糊时段用 point（center 填该时刻）；完全没提时间用 none。
- 测点用标准字段名：振动类用 v1/v3，瓦温/轴承温度用 bearing_temp，油压用 oil_pressure，电流用 current，转速用 speed。
- 不确定的设备号填 null，不要猜。"""


_RE_DEVICE = re.compile(r"FJ[-\s]?0?([1-4])", re.IGNORECASE)
_RE_AR_DEVICE = re.compile(r"(\d{1,2})\s*号\s*(?:机|机组|风机|引风机)")
_RE_CN_DEVICE = re.compile(r"([一二两三四])\s*号\s*(?:机|机组|风机|引风机)")
_CN_DEVICE_NUM = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4}
_SENSOR_WORDS = [
    (("振动", "震动", "抖动", "晃"), ["v1", "v3"]),
    (("瓦温", "轴承温度", "温度", "发热", "烫"), ["bearing_temp"]),
    (("油压", "供油压力", "压力"), ["oil_pressure"]),
    (("电流", "电气"), ["current"]),
    (("转速", "超速"), ["speed"]),
]
_DIAG_WORDS = ("故障", "检修", "报警", "异常", "振动", "震动", "温度", "瓦温", "油压", "压力",
               "电流", "转速", "异响", "声音", "漏油", "喘振", "跳机", "跳车", "停机", "坏了", "排查")


def _extract_device(text: str) -> str | None:
    """识别设备位号：FJ-01 / 1号机 / 三号风机 …（识别不出就返回 None，交由澄清流程处理）"""
    text = text or ""
    m = _RE_DEVICE.search(text)
    if m:
        candidate = f"FJ-0{m.group(1)}"
        return candidate if candidate in thresholds.device_ids() else None
    for regex, convert in ((_RE_AR_DEVICE, int), (_RE_CN_DEVICE, _CN_DEVICE_NUM.get)):
        m = regex.search(text)
        if m:
            number = convert(m.group(1))
            if number:
                candidate = f"FJ-0{int(number)}"
                return candidate if candidate in thresholds.device_ids() else None
    return None


def _extract_sensors(text: str) -> list[str]:
    hits: list[str] = []
    for words, sensors in _SENSOR_WORDS:
        if any(w in (text or "") for w in words):
            for s in sensors:
                if s not in hits:
                    hits.append(s)
    return hits


def recognize_by_rules(query: str, now: datetime | None = None) -> IntentResult:
    """LLM 不可用时的回退：正则抽设备 + 时间词 + 测点词。"""
    device_id = _extract_device(query)
    sensors = _extract_sensors(query)
    is_diag = bool(device_id or sensors or any(w in (query or "") for w in _DIAG_WORDS))
    time_expr = parse_time_expression(query, now=now)
    missing = [] if device_id else ["device_id"]
    return IntentResult(
        intent="equipment_diagnosis" if is_diag else "other",
        device_id=device_id,
        time_expression=time_expr,
        sensor_hint=sensors,
        symptom=(query or "").strip()[:120] or None,
        missing_slots=missing if is_diag else [],
        confidence=0.55,
        raw_query=query,
    )


def recognize_by_llm(query: str, now: datetime | None = None) -> IntentResult:
    from packages.core.config import settings
    from packages.llm.client import client

    today = (now or datetime.now(TZ)).strftime("%Y-%m-%d %H:%M")
    resp = client.chat.completions.create(
        model=settings.DEEPSEEK_MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"当前时间：{today}（+08:00）\n用户提问：{query}"},
        ],
        temperature=0.0,
        response_format={"type": "json_object"},
    )
    payload = json.loads(resp.choices[0].message.content or "{}")
    result = IntentResult(
        intent=payload.get("intent") or "other",
        device_id=payload.get("device_id"),
        time_expression=TimeExpression(**(payload.get("time_expression") or {"type": "none"})),
        sensor_hint=payload.get("sensor_hint") or [],
        symptom=payload.get("symptom"),
        confidence=float(payload.get("confidence") or 0.0),
        raw_query=query,
    )
    if result.device_id and result.device_id not in thresholds.device_ids():
        result.device_id = None
    if result.intent == "equipment_diagnosis":
        result.missing_slots = [] if result.device_id else ["device_id"]
    return result


def recognize(query: str, use_llm: bool = True, now: datetime | None = None) -> tuple[IntentResult, str]:
    """A1 入口：返回 (IntentResult, 使用的通道)。"""
    if use_llm:
        try:
            return recognize_by_llm(query, now=now), "llm"
        except Exception as exc:            # 配额/网络/解析失败 -> 规则回退，不打断链路
            fallback = recognize_by_rules(query, now=now)
            fallback.symptom = (fallback.symptom or "") + f"（LLM 不可用，已回退规则解析：{type(exc).__name__}）"
            return fallback, "rules"
    return recognize_by_rules(query, now=now), "rules"


def build_clarification_card(result: IntentResult) -> DiagnosisCard:
    """缺设备位号时的澄清卡片（决策 D2：强制澄清，禁止猜测）。"""
    options = []
    for device_id in thresholds.device_ids():
        device = thresholds.get_device(device_id)
        options.append({
            "device_id": device_id,
            "label": f"{device_id}（{device['model']}，额定 {device['rated_speed']} r/min）",
        })
    return DiagnosisCard(
        type="clarification_card",
        summary="请先确认要诊断的设备位号，我再继续分析。",
        window_note="",
        options=options,
        actions=[CardAction(key="select_device", label="选择设备")],
        notes=["未指定设备时不会猜测机组：FJ-01/02/03 为同类型离心引风机，故障判据与阈值不同。"],
    )
