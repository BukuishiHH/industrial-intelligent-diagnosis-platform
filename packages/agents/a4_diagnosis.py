# -*- coding: utf-8 -*-
"""A4 证据融合与根因推理节点（设计文档 §3.2 术语更正：不是"校验"，而是推理）。

输入：A2 的知识片段（带 locator）+ A3 的传感器特征摘要 + 设备档案/阈值
输出：DiagnosisResult（结构化）

关键约束：
- **一次 LLM 调用**完成推理（MVP 不做多轮反思循环），温度 0，response_format=json_object。
- **强制引用**：每条 evidence 的 ref 必须能对上任一手册 locator 或实测数据标识；
  对不上的证据被丢弃并记入校验问题（防幻觉）。
- 证据不足时输出 need_more_info 与 evidence_gaps，而不是编造结论。
"""
from __future__ import annotations

import json
import os
from datetime import datetime

from packages.core import thresholds
from packages.core.timewindow import TZ
from packages.schemas.diagnosis import (
    CandidateCause,
    DiagnosisResult,
    Evidence,
    IntentResult,
    RetrievedChunk,
    RootCause,
    SensorDigest,
    Solution,
    SolutionStep,
)

SYSTEM_PROMPT = """你是工业设备（离心引风机）故障诊断专家。你会收到三部分信息：
1) 设备档案与该机型的报警/停机阈值；
2) 现场实测数据的特征摘要（含阈值与趋势规则命中情况）；
3) 从该设备手册（故障案例手册、维修手册、操作手册）中检索到的知识片段，每段带定位编号。

推理要求：
- 以"知识为依据、数据为证据"做假设—验证：先用数据特征筛选可能的故障类型，再用手册案例佐证。
- 数据特征与手册案例**必须一致**才能作为根因；只有知识没有数据支撑的假设，置信度不得高于 0.5。
- 数据里出现的现象（如"上升集中在最后 1h、属突变型"）要用于区分渐进性故障（积灰结垢）与突发性故障（碰磨、轴承损伤、对中破坏）。
- 每条证据的 ref 必须是给定材料中真实存在的定位编号（手册片段的定位编号原样填写；数据证据写"测点名@时间窗"），不得编造。
- 若证据不足以判断，设置 need_more_info=true 并在 evidence_gaps 中说明缺什么，不要强行给出根因。
- 处置步骤优先引用维修手册/案例手册中的做法，并给出必要的安全提示。
- 只输出 JSON，不要输出任何额外文字。
- **输出规模必须克制**（直接影响响应时间）：candidate_causes 最多 4 个（按置信度排序，只保留有依据的）；
  每个候选最多 2 条证据，每条 statement ≤ 40 字；solution.steps 3~6 条，每条 action ≤ 50 字；
  safety_notes ≤ 3 条；evidence_gaps ≤ 3 条；symptoms ≤ 4 条。所有文字精炼，不要复述材料。

输出 JSON 结构：
{
  "symptoms": ["故障现象的客观描述"],
  "candidate_causes": [
    {"code": "ROTOR_UNBALANCE|RUB_IMPACT|COUPLING_DAMAGE|BEARING_DAMAGE|BEARING_TEMP_HIGH|LUBRICATION_FAULT|ELECTRICAL_FAULT|SURGE|BASE_LOOSENESS|UNKNOWN",
     "name": "故障名称（≤15 字）", "confidence": 0.0-1.0,
     "evidence": [{"source": "manual|sensor", "ref": "定位编号", "statement": "≤40 字"}]}
  ],
  "root_cause": {"code": "...", "name": "...", "confidence": 0.0-1.0, "basis": "为什么排除其他可能"},
  "solution": {"urgency": "立即停机|紧急停机|计划停机|运行观察",
               "steps": [{"no": 1, "action": "具体动作", "ref": "依据定位编号"}],
               "safety_notes": ["安全提示"]},
  "evidence_gaps": ["还缺什么证据"],
  "need_more_info": false,
  "overall_confidence": 0.0-1.0
}"""


def _device_profile_text(device_id: str) -> str:
    device = thresholds.get_device(device_id)
    lines = [f"设备 {device_id}，型号 {device['model']}，额定转速 {device['rated_speed']} r/min，"
             f"轴承形式 {'滚动轴承' if device.get('bearing_type') == 'rolling' else '滑动轴承（瓦温）'}"]
    for sensor, spec in device["points"].items():
        normal = spec.get("normal", {})
        alarm = spec.get("alarm", {})
        trip = spec.get("trip", {})
        def fmt(d):
            if "high" in d and "low" in d:
                return f"{d['low']}~{d['high']}"
            return f"≤{d['max']}" if "max" in d else (f"≥{d['min']}" if "min" in d else "—")
        lines.append(f"  {sensor}({spec.get('unit', '')})：正常区 {fmt(normal)}，报警 {fmt(alarm)}，停机 {fmt(trip)}"
                     f"；别名 {', '.join(spec.get('aliases', [])[:3])}")
    return "\n".join(lines)


DOC_TYPE_CN = {"case": "故障案例手册", "maintenance": "维修手册", "operation": "设备操作手册"}


def _knowledge_text(chunks: list[RetrievedChunk]) -> tuple[str, set[str]]:
    lines, locators = [], set()
    for c in chunks:
        locator = c.locator or c.chunk_id
        locators.add(locator)
        locators.add(c.chunk_id)
        title = f"（{c.case_no}）" if c.case_no else ""
        doc_cn = DOC_TYPE_CN.get(c.doc_type or "", c.doc_type or "")
        lines.append(f"[{locator}] {c.device_id} {doc_cn}{title}\n{c.text}")
    return "\n\n".join(lines), locators


def build_user_prompt(query: str, intent: IntentResult, digest: SensorDigest,
                      chunks: list[RetrievedChunk], device_id: str) -> tuple[str, set[str]]:
    knowledge, locators = _knowledge_text(chunks)
    data_block = "\n".join(digest.summary_lines) if digest and digest.summary_lines else "（无实测数据）"
    missing = []
    if not chunks:
        missing.append("知识检索无结果：结论缺少手册依据，置信度必须下调")
    if not digest or digest.empty:
        missing.append("无实测数据：结论缺少数据依据，置信度必须下调")

    prompt = f"""# 设备档案
{_device_profile_text(device_id)}

# 用户提问
{query}
（识别到的槽位：设备 {device_id}，症状 {intent.symptom or '未明确'}，关注测点 {', '.join(intent.sensor_hint) or '全部'}）

# 实测数据特征摘要
{data_block}

# 手册知识片段（每条方括号内为定位编号，证据 ref 请原样填写）
{knowledge or '（无）'}

# 附加要求
{chr(10).join('- ' + m for m in missing) if missing else '- 知识与数据证据均齐备'}
"""
    return prompt, locators


def _validate_evidence(result: DiagnosisResult, locators: set[str], digest: SensorDigest) -> list[str]:
    """程序化校验引用：ref 必须对得上手册定位编号或实测数据标识，否则丢弃该证据。"""
    problems: list[str] = []
    sensor_refs = {f"{s.sensor}@{digest.device_id}" for s in digest.sensors} if digest else set()
    for hit in (digest.trend_hits if digest else []):
        sensor_refs.add(hit.rule_id)

    def ok(ref: str, source: str) -> bool:
        if not ref:
            return False
        if source == "manual":
            return any(loc in ref or ref in loc for loc in locators if loc)
        return any(k in ref for k in sensor_refs) or "@" in ref or "10min" in ref or "24h" in ref

    for cause in result.candidate_causes:
        kept = []
        for ev in cause.evidence:
            if ok(ev.ref, ev.source):
                kept.append(ev)
            else:
                problems.append(f"丢弃无法溯源的证据：{cause.name} / {ev.ref}")
        cause.evidence = kept
    if result.root_cause:
        if not any(c.code == result.root_cause.code and c.evidence for c in result.candidate_causes):
            problems.append("根因缺少可溯源证据，已下调置信度")
            result.root_cause.confidence = min(result.root_cause.confidence, 0.4)
            result.overall_confidence = min(result.overall_confidence, 0.4)
    return problems


def diagnose(query: str, intent: IntentResult, digest: SensorDigest,
             chunks: list[RetrievedChunk], use_llm: bool = True) -> tuple[DiagnosisResult, dict]:
    device_id = intent.device_id or digest.device_id
    trace: dict = {"llm": use_llm, "chunks": len(chunks), "prompt_chars": 0}

    if not chunks and (digest is None or digest.empty):
        return DiagnosisResult(
            device_id=device_id, need_more_info=True,
            evidence_gaps=["既无知识依据也无实测数据，无法给出结论"],
            overall_confidence=0.0,
        ), trace

    prompt, locators = build_user_prompt(query, intent, digest, chunks, device_id)
    trace["prompt_chars"] = len(prompt)

    if not use_llm:
        raise RuntimeError("A4 必须使用 LLM")

    from packages.core.config import settings
    from packages.llm.client import client

    from packages.llm.json_utils import parse_json_response

    llm = client.with_options(timeout=float(os.getenv("A4_TIMEOUT", "45")), max_retries=0)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
    payload: dict = {}
    for attempt in (1, 2):
        resp = llm.chat.completions.create(
            model=settings.DEEPSEEK_MODEL_NAME,
            messages=messages,
            temperature=0.0,
            response_format={"type": "json_object"},
            # 显式给足输出预算：默认上限偏小会把结构化结论截断成非法 JSON
            max_tokens=int(os.getenv("A4_MAX_TOKENS", "2600")),
        )
        content = resp.choices[0].message.content or ""
        finish = getattr(resp.choices[0], "finish_reason", None)
        trace["tokens"] = getattr(resp.usage, "total_tokens", None)
        trace["finish_reason"] = finish
        try:
            payload = parse_json_response(content)
            break
        except ValueError as exc:
            trace["parse_error"] = str(exc)[:200] + "（finish_reason=" + str(finish) + "）"
            if attempt == 2:
                raise
            messages = messages + [
                {"role": "assistant", "content": content[:500]},
                {"role": "user", "content": "上面的输出不是合法 JSON。请重新只输出一个完整的 JSON 对象，"
                                            "不要任何解释文字，并控制在 2000 token 以内。"},
            ]

    result = DiagnosisResult(
        device_id=device_id,
        device_model=thresholds.get_device(device_id).get("model"),
        start=digest.start if digest else None,
        end=digest.end if digest else None,
        symptoms=payload.get("symptoms") or [],
        candidate_causes=[
            CandidateCause(
                code=(c.get("code") or "UNKNOWN"),
                name=c.get("name") or "",
                confidence=float(c.get("confidence") or 0.0),
                evidence=[Evidence(source=e.get("source", "manual"), ref=e.get("ref", ""),
                                   statement=e.get("statement", "")) for e in (c.get("evidence") or [])],
            ) for c in (payload.get("candidate_causes") or [])
        ],
        solution=Solution(
            urgency=(payload.get("solution") or {}).get("urgency", "运行观察"),
            steps=[SolutionStep(no=int(s.get("no") or i + 1), action=s.get("action", ""), ref=s.get("ref"))
                   for i, s in enumerate((payload.get("solution") or {}).get("steps") or [])],
            safety_notes=(payload.get("solution") or {}).get("safety_notes") or [],
        ),
        evidence_gaps=payload.get("evidence_gaps") or [],
        need_more_info=bool(payload.get("need_more_info")),
        overall_confidence=float(payload.get("overall_confidence") or 0.0),
        data_quality=digest.data_quality if digest else None,
        threshold_hits=[f"{h.sensor} {h.level}: {h.description}" for h in (digest.threshold_hits if digest else [])]
                        + [f"{t.sensor} {t.rule_id}: {t.detail}" for t in (digest.trend_hits if digest else [])],
        references={"a2_chunks": [c.locator or c.chunk_id for c in chunks],
                    "a3_query": {"device_id": device_id, "sensors": [s.sensor for s in (digest.sensors if digest else [])]}},
        model={"name": settings.DEEPSEEK_MODEL_NAME, "prompt_version": "diag_v1"},
        created_at=datetime.now(TZ),
    )
    rc = payload.get("root_cause") or {}
    if rc:
        result.root_cause = RootCause(code=rc.get("code") or "UNKNOWN", name=rc.get("name") or "",
                                      confidence=float(rc.get("confidence") or 0.0), basis=rc.get("basis") or "")

    problems = _validate_evidence(result, locators, digest)
    trace["validation_problems"] = problems
    return result, trace
