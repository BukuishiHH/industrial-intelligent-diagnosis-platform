# -*- coding: utf-8 -*-
"""端到端（A1 -> A3 -> A2 -> A4 -> A5）+ 耗时统计"""
import time
from packages.agents.a1_intent import recognize
from packages.core.timewindow import resolve_window
from packages.agents.a3_data import compute_digest
from packages.rag.retriever import hybrid_search
from packages.agents.a4_diagnosis import diagnose
from packages.agents.a5_report import generate_report
from packages.schemas.diagnosis import HitlDecision
from packages.core.timewindow import TZ
from datetime import datetime

QUERY = "FJ-01 最近振动一直往上涨，是什么原因？"
DATA = "data/raw_docs/设备传感器仿真数据_72h_unbalance_fj01.csv"
marks = {}
t0 = time.time()
intent, ch = recognize(QUERY); marks["A1"] = time.time() - t0
start, end, note, _ = resolve_window(intent.time_expression)
t = time.time(); digest = compute_digest(intent.device_id, start, end, data_path=DATA); marks["A3"] = time.time() - t
t = time.time(); chunks, trace = hybrid_search(QUERY, device_id=intent.device_id, top_p=5); marks["A2"] = time.time() - t
t = time.time(); result, atrace = diagnose(QUERY, intent, digest, chunks); marks["A4"] = time.time() - t
result.diagnosis_id = "dg_test_0001"
hitl = HitlDecision(decision="confirm", reviewer_user_id=1, decided_at=datetime.now(TZ))
t = time.time(); md, meta = generate_report(result, digest, chunks, hitl); marks["A5"] = time.time() - t
marks["总计"] = time.time() - t0

for k, v in marks.items():
    print(f"  {k}: {v:.1f}s")
print(f"\n[A4] tokens={atrace.get('tokens')} prompt={atrace['prompt_chars']} 字")
print(f"  根因: {result.root_cause.name} conf={result.root_cause.confidence}")
print(f"  候选数={len(result.candidate_causes)} 证据={sum(len(c.evidence) for c in result.candidate_causes)} "
      f"步骤={len(result.solution.steps)} 安全={len(result.solution.safety_notes)} 缺口={len(result.evidence_gaps)}")
print(f"  校验问题: {atrace.get('validation_problems')}")
print(f"\n[A5] 报告 {meta['chars']} 字")
print("-" * 80)
print("\n".join(md.split("\n")[:46]))
print("...")
