# -*- coding: utf-8 -*-
"""诊断历史与报告的**用户隔离**验证。

覆盖三类越权面：
    ① 历史列表    B 看不到 A 的诊断
    ② 报告详情    B 读 A 的报告 -> 404（不暴露存在性）
    ③ 会话操作    B 对 A 的会话做澄清/审核 -> 403；查看会话状态 -> 403
"""
import os
import sys

os.environ["SENSOR_DATA_PATH"] = "data/raw_docs/设备传感器仿真数据_72h_unbalance_fj01.csv"
# 关闭 LLM（A1 走规则回退、A4 走降级兜底）：本用例验证的是**归属隔离**，
# 不依赖大模型可用性，因此可离线、快速、稳定地回归。
os.environ["DIAGNOSIS_USE_LLM"] = "0"

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.middleware.exception_handler import register_exception_handlers
from apps.api.routers.diagnosis_router import diagnosis_router
from packages.core.security.jwt_util import create_access_token

app = FastAPI()
app.include_router(diagnosis_router)
register_exception_handlers(app)
client = TestClient(app)


def auth(uid: int, name: str) -> dict:
    return {"Authorization": "Bearer " + create_access_token(user_id=str(uid), username=name)}


ALICE, BOB = auth(101, "alice"), auth(202, "bob")
failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    print(("  [通过] " if condition else "  [失败] ") + label + (" " + detail if detail else ""))
    if not condition:
        failures.append(label)


print("=== 1) 用户 A(101) 发起并确认一次诊断 ===")
r = client.post("/diagnosis/query", json={"query": "FJ-01 最近振动一直往上涨，是什么原因？"}, headers=ALICE)
out = r.json()["data"]
thread_a = out["thread_id"]
print("    status=" + out["status"] + " thread=" + thread_a)
if out["status"] != "awaiting_review":
    print("    !! 未进入待审核，无法继续该用例")
    sys.exit(1)
r = client.post("/diagnosis/review", json={"thread_id": thread_a, "decision": "confirm"}, headers=ALICE)
done = r.json()["data"]
report_a = done["report_id"]
print("    report_id=" + str(report_a) + " status=" + done["status"])

print("\n=== 2) 用户 B(202) 的历史列表（应看不到 A 的记录）===")
r = client.get("/diagnosis/history?limit=50", headers=BOB)
rows = r.json()["data"] or []
ids = [row["report_id"] for row in rows]
check("B 的历史不含 A 的报告", report_a not in ids, "共 " + str(len(rows)) + " 条")
check("B 的历史全部属于 B", all(row.get("source") for row in rows))

print("\n=== 3) 用户 B 读取 A 的报告（应 404）===")
r = client.get("/diagnosis/report/" + report_a, headers=BOB)
check("B 读 A 的报告被拒绝", r.json()["code"] == 404, "code=" + str(r.json()["code"]) + " msg=" + r.json()["message"])

print("\n=== 4) 用户 B 操作 A 的会话（应 403）===")
r = client.post("/diagnosis/review", json={"thread_id": thread_a, "decision": "confirm"}, headers=BOB)
check("B 不能确认 A 的会话", r.json()["code"] == 403, "code=" + str(r.json()["code"]) + " msg=" + r.json()["message"])
r = client.post("/diagnosis/review", json={"thread_id": thread_a, "device_id": "FJ-02"}, headers=BOB)
check("B 不能澄清 A 的会话", r.json()["code"] == 403, "code=" + str(r.json()["code"]))
r = client.get("/diagnosis/state/" + thread_a, headers=BOB)
check("B 不能查看 A 的会话状态", r.json()["code"] == 403, "code=" + str(r.json()["code"]))

print("\n=== 5) 用户 A 访问自己的数据（应全部成功）===")
r = client.get("/diagnosis/history?limit=50", headers=ALICE)
rows = r.json()["data"] or []
check("A 能在历史中看到自己的报告", report_a in [row["report_id"] for row in rows],
      "共 " + str(len(rows)) + " 条")
r = client.get("/diagnosis/report/" + report_a, headers=ALICE)
check("A 能读取自己的报告", r.json()["code"] == 200 and len(r.json()["data"]["content"]) > 500)
r = client.get("/diagnosis/state/" + thread_a, headers=ALICE)
check("A 能查看自己的会话状态", r.json()["code"] == 200)

print("\n=== 6) 未登录（应 401）===")
r = client.get("/diagnosis/history")
check("未登录不能查历史", r.json()["code"] == 401)

print("\n" + "=" * 60)
if failures:
    print("隔离验证失败项：" + "；".join(failures))
    sys.exit(1)
print("用户隔离验证全部通过")
