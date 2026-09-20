# -*- coding: utf-8 -*-
"""持久化端到端验证（两阶段，跨进程）：

    phase 1：发起诊断（跑到"待审核"中断）-> 把 thread_id 存盘
    phase 2：**另起一个进程**恢复该会话 -> 确认 -> 校验 MySQL 落库

跨进程能恢复，说明 checkpoint 已持久化（不是内存态）。
"""
import json
import sys
from pathlib import Path

PHASE = sys.argv[1] if len(sys.argv) > 1 else "1"
DATA = "data/raw_docs/设备传感器仿真数据_72h_unbalance_fj01.csv"
STATE_FILE = Path("data/checkpoints/_e2e_thread.json")

from packages.service.diagnosis_service import DiagnosisService

if PHASE == "1":
    svc = DiagnosisService(data_path=DATA)
    print("checkpoint backend:", svc.checkpoint_backend)
    out = svc.start("FJ-01 最近振动一直往上涨，是什么原因？", user_id=99)
    print("status:", out["status"], "| thread:", out["thread_id"], "| timings:", out["timings"])
    assert out["status"] == "awaiting_review", "未进入待审核状态：" + str(out["status"])
    card = out["payload"]["card"]
    print("summary:", card["summary"])
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({"thread_id": out["thread_id"],
                                      "diagnosis_id": out["payload"]["diagnosis_id"]}), encoding="utf-8")
    print("已保存 thread_id 到", STATE_FILE)

else:
    saved = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    svc = DiagnosisService(data_path=DATA)          # 全新进程、全新实例
    print("checkpoint backend:", svc.checkpoint_backend, "| 恢复 thread:", saved["thread_id"])
    snap = svc.state_of(saved["thread_id"])
    print("恢复出的会话状态：next =", snap["next"], "| 有诊断结论 =", bool(snap["values"].get("report_id") is None))
    out = svc.resume(saved["thread_id"], {"decision": "confirm", "user_id": 99})
    print("resume 后 status:", out["status"], "| report_id:", out["report_id"])
    assert out["status"] == "completed"

    print("\n=== MySQL 落库校验 ===")
    from sqlalchemy import text
    from packages.core.database import session_factory
    session = session_factory()
    try:
        for table in ("diagnosis_record", "diagnosis_evidence", "hitl_review", "diagnosis_report"):
            n = session.execute(text("SELECT COUNT(*) FROM " + table)).scalar()
            print(f"  {table}: {n} 行")
        row = session.execute(text(
            "SELECT diagnosis_id, device_id, status, root_cause_name, root_cause_confidence, urgency, "
            "user_id, thread_id FROM diagnosis_record ORDER BY id DESC LIMIT 1")).mappings().first()
        print("  最新诊断记录:", dict(row))
        ev = session.execute(text(
            "SELECT source, ref, LEFT(statement, 30) AS stmt FROM diagnosis_evidence "
            "WHERE diagnosis_id = :d LIMIT 4"), {"d": row["diagnosis_id"]}).mappings().all()
        for e in ev:
            print("    证据:", dict(e))
        rep = session.execute(text(
            "SELECT report_id, chars, file_path FROM diagnosis_report WHERE diagnosis_id = :d"),
            {"d": row["diagnosis_id"]}).mappings().first()
        print("  报告:", dict(rep) if rep else None)
        rev = session.execute(text(
            "SELECT decision, reviewer_user_id FROM hitl_review WHERE diagnosis_id = :d"),
            {"d": row["diagnosis_id"]}).mappings().all()
        print("  审核:", [dict(x) for x in rev])
    finally:
        session.close()

    from packages.service.persistence import load_record, load_report
    rec = load_record(out["report_id"])
    print("  load_record source:", rec["source"], "| status:", rec["status"])
    print("  load_report 前 60 字:", (load_report(out["report_id"]) or "")[:60].replace("\n", " "))
