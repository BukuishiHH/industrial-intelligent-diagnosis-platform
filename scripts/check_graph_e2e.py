# -*- coding: utf-8 -*-
"""LangGraph 图 + 服务层端到端：澄清中断 -> 恢复 -> 审核中断 -> 确认 -> 报告落盘"""
import time, json
from packages.service.diagnosis_service import DiagnosisService

DATA = "data/raw_docs/设备传感器仿真数据_72h_unbalance_fj01.csv"
svc = DiagnosisService(data_path=DATA)

print("=== 场景 1：缺设备位号 -> 澄清 ===")
t0 = time.time()
out = svc.start("最近振动一直往上涨，什么原因？", user_id=7)
print("status:", out["status"])
print("澄清选项:", [o["label"] for o in (out["payload"]["card"]["options"] if out["payload"] else [])][:3])
th = out["thread_id"]

print("\n=== 场景 1 恢复：选择 FJ-01 -> 诊断 -> 待审核 ===")
out = svc.resume(th, {"device_id": "FJ-01"})
print("status:", out["status"], "| timings:", out["timings"])
card = out["payload"]["card"]
print("summary:", card["summary"])
print("window:", card["window_note"])
print("步骤数:", len(card["solution_steps"]), "| 证据组:", [(g["source"], len(g["items"])) for g in card["evidence_groups"]])
print("actions:", card["actions"])
did = out["payload"]["diagnosis_id"]

print("\n=== 场景 1 恢复：确认 -> 生成报告 ===")
out = svc.resume(th, {"decision": "confirm", "user_id": 7})
print("status:", out["status"], "| report_id:", out["report_id"], "| 耗时:", out["timings"])
print("报告字数:", len(out["report_markdown"] or ""))
print("总耗时: %.1fs" % (time.time() - t0))

print("\n=== 场景 2：完整提问（不需要澄清）===")
t0 = time.time()
out = svc.start("FJ-01 最近振动一直往上涨，是什么原因？", user_id=7)
print("status:", out["status"], "| timings:", out["timings"], "| 总耗时 %.1fs" % (time.time() - t0))
if out["status"] == "awaiting_review":
    print("summary:", out["payload"]["card"]["summary"])
    out2 = svc.resume(out["thread_id"], {"decision": "confirm", "user_id": 7})
    print("确认后 report_id:", out2["report_id"])

print("\n=== 场景 3：非检修意图 ===")
out = svc.start("今天天气怎么样？", user_id=7)
print("status:", out["status"], "| errors:", out["errors"])

print("\n=== 报告历史 ===")
for r in svc.history(3):
    print(" ", r["report_id"], r["device_id"], r["root_cause"] and r["root_cause"]["name"])
