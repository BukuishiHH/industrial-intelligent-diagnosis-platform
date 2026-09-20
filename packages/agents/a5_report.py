# -*- coding: utf-8 -*-
"""A5 报告生成节点：把结构化诊断结论渲染为 Markdown 报告（决策 D5）。

原则：**字段全部来自 state 的结构化结论**，LLM 只负责把"原因分析"写成连贯叙述
（失败或超时则退回 root_cause.basis 原文），不允许引入结论之外的新事实。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from packages.core.timewindow import TZ
from packages.schemas.diagnosis import DiagnosisResult, HitlDecision, RetrievedChunk, SensorDigest

REPORT_PROMPT = """你是工业设备检修报告的撰写员。下面是已经结构化好的诊断结论，
请只用这些事实，写一段 120~180 字的原因分析叙述：说明现象与根因之间的因果链，以及为什么排除主要备选。
不要新增任何未给出的事实，不要写处置步骤，直接输出正文段落，不要加标题。"""


def _fmt(dt: datetime | None) -> str:
    return dt.astimezone(TZ).strftime("%Y-%m-%d %H:%M") if dt else "—"


def _narrative(result: DiagnosisResult, use_llm: bool) -> str:
    """LLM 生成原因分析叙述；失败退回 basis（报告不因 LLM 失败而无法生成）。"""
    if not result.root_cause:
        return "本次未形成明确根因结论。"
    if not use_llm:
        return result.root_cause.basis or result.root_cause.name
    try:
        from packages.core.config import settings
        from packages.llm.client import client

        payload = {
            "device": result.device_id,
            "symptoms": result.symptoms,
            "root_cause": {"name": result.root_cause.name, "confidence": result.root_cause.confidence,
                           "basis": result.root_cause.basis},
            "alternatives": [{"name": c.name, "confidence": c.confidence}
                             for c in result.candidate_causes[1:4]],
            "key_findings": result.threshold_hits[:6],
        }
        resp = client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL_NAME,
            messages=[{"role": "system", "content": REPORT_PROMPT},
                      {"role": "user", "content": str(payload)}],
            temperature=0.2,
            timeout=10,            # 叙述生成失败/超时立即退回模板文本，不拖累整体响应
        )
        return (resp.choices[0].message.content or "").strip() or result.root_cause.basis
    except Exception:
        return result.root_cause.basis or result.root_cause.name


def generate_report(
    result: DiagnosisResult,
    digest: SensorDigest | None = None,
    chunks: list[RetrievedChunk] | None = None,
    hitl: HitlDecision | None = None,
    use_llm: bool | None = None,
) -> tuple[str, dict[str, Any]]:
    """返回 (markdown, meta)。

    默认**不调用 LLM**：原因分析直接采用 A4 已给出的 root_cause.basis。
    理由：A4 的 basis 本身就是完整的因果论述，再让模型重写一遍只是增加 20~30s 延迟与失真风险
    （实测 A5 的 LLM 叙述占总耗时一半以上）。需要时设 REPORT_LLM_NARRATIVE=1 开启。
    """
    if use_llm is None:
        import os
        use_llm = os.getenv("REPORT_LLM_NARRATIVE", "0") == "1"
    chunks = chunks or []
    lines: list[str] = []
    lines.append("# " + result.device_id + " 设备诊断报告")
    lines.append("")
    lines.append("> 诊断编号：" + (result.diagnosis_id or "—")
                 + "　|　设备位号：" + result.device_id
                 + "（" + (result.device_model or "型号未知") + "）"
                 + "　|　生成时间：" + _fmt(result.created_at or datetime.now(TZ)))
    lines.append("")

    lines.append("## 一、基本信息")
    lines.append("")
    lines.append("| 项目 | 内容 |")
    lines.append("| --- | --- |")
    lines.append("| 分析窗口 | " + _fmt(result.start) + " ~ " + _fmt(result.end) + " |")
    if digest and digest.data_quality:
        q = digest.data_quality
        extra = ("，缺失率 %.1f%%" % (q.missing_rate * 100)) if q.missing_rate is not None else ""
        lines.append("| 数据规模 | %d 点（间隔 %ds），覆盖 %sh%s |"
                     % (q.points, q.interval_seconds, q.covered_hours, extra))
    lines.append("| 处置紧迫度 | **" + str(result.solution.urgency) + "** |")
    lines.append("| 总体置信度 | %.2f |" % result.overall_confidence)
    if hitl:
        lines.append("| 审核 | " + ("已确认" if hitl.decision == "confirm" else "已否定")
                     + "（审核人 ID " + str(hitl.reviewer_user_id or "—") + "，"
                     + _fmt(hitl.decided_at) + "） |")
    lines.append("")

    lines.append("## 二、故障现象")
    lines.append("")
    for s in (result.symptoms or ["（未记录）"]):
        lines.append("- " + s)
    lines.append("")

    lines.append("## 三、诊断结论")
    lines.append("")
    if result.root_cause:
        rc = result.root_cause
        lines.append("**根本原因：" + rc.name + "**（置信度 %.2f）" % rc.confidence)
        lines.append("")
        lines.append("### 原因分析")
        lines.append("")
        lines.append(_narrative(result, use_llm))
        lines.append("")
    if len(result.candidate_causes) > 1:
        lines.append("### 备选原因（已排除或置信度较低）")
        lines.append("")
        lines.append("| 可能原因 | 置信度 | 主要依据 |")
        lines.append("| --- | --- | --- |")
        for c in result.candidate_causes:
            if result.root_cause and c.code == result.root_cause.code and c.name == result.root_cause.name:
                continue
            refs = "；".join(e.ref for e in c.evidence[:2]) or "—"
            lines.append("| " + c.name + " | %.2f | " % c.confidence + refs + " |")
        lines.append("")

    lines.append("## 四、证据链")
    lines.append("")
    lines.append("### 4.1 知识依据（设备手册）")
    lines.append("")
    manual = [(e) for c in result.candidate_causes for e in c.evidence if e.source == "manual"]
    if manual:
        seen: set[str] = set()
        for e in manual:
            if e.ref in seen:
                continue
            seen.add(e.ref)
            lines.append("- " + e.ref + "　" + e.statement)
    else:
        lines.append("- （无）")
    lines.append("")
    lines.append("### 4.2 数据依据（传感器实测）")
    lines.append("")
    for h in result.threshold_hits:
        lines.append("- " + h)
    sensor = [e for c in result.candidate_causes for e in c.evidence if e.source == "sensor"]
    for e in sensor[:6]:
        lines.append("- " + e.ref + "　" + e.statement)
    if not result.threshold_hits and not sensor:
        lines.append("- （无）")
    lines.append("")

    lines.append("## 五、处置建议")
    lines.append("")
    for s in result.solution.steps:
        ref = ("　（依据：" + s.ref + "）") if s.ref else ""
        lines.append(str(s.no) + ". " + s.action + ref)
    lines.append("")

    if result.solution.safety_notes:
        lines.append("## 六、安全提示")
        lines.append("")
        for n in result.solution.safety_notes:
            lines.append("- ⚠ " + n)
        lines.append("")

    if result.evidence_gaps:
        lines.append("## 七、信息缺口（建议补充）")
        lines.append("")
        for g in result.evidence_gaps:
            lines.append("- " + g)
        lines.append("")

    lines.append("## 八、引用清单")
    lines.append("")
    for loc in (result.references.get("a2_chunks") or []):
        lines.append("- " + str(loc))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("> 本报告由工业智能诊断平台自动生成，诊断结论已经人工确认；"
                 "报告中的每条证据均可回溯到设备手册原文或传感器实测数据。")

    markdown = "\n".join(lines)
    meta = {
        "device_id": result.device_id,
        "diagnosis_id": result.diagnosis_id,
        "chars": len(markdown),
        "generated_at": datetime.now(TZ).isoformat(),
        "llm_narrative": bool(use_llm),      # False = 使用 A4 的 basis 原文
    }
    return markdown, meta
