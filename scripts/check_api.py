# -*- coding: utf-8 -*-
"""诊断接口测试：澄清 -> 审核 -> 报告（挂载路由到临时 app，避免依赖 MySQL 启动）"""
import time
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.routers.diagnosis_router import diagnosis_router
from packages.core.security.jwt_util import create_access_token

app = FastAPI()
app.include_router(diagnosis_router)
from apps.api.middleware.exception_handler import register_exception_handlers
register_exception_handlers(app)
client = TestClient(app)
token = create_access_token(user_id="7", username="tester")
H = {"Authorization": "Bearer " + token}

print("=== 1) 非检修意图（快路径）===")
r = client.post("/diagnosis/query", json={"query": "今天天气怎么样？"}, headers=H)
print(r.status_code, r.json()["code"], r.json()["message"], "| status:", r.json()["data"]["status"])

print("\n=== 2) 缺设备 -> 澄清 ===")
r = client.post("/diagnosis/query", json={"query": "最近振动一直往上涨，什么原因？"}, headers=H)
d = r.json()["data"]
print(r.status_code, "status:", d["status"], "| thread:", d["thread_id"])
opts = d["payload"]["card"]["options"]
print("选项:", [o["device_id"] for o in opts])

print("\n=== 3) 澄清回答 -> 诊断 -> 待审核 ===")
t0 = time.time()
r = client.post("/diagnosis/review", json={"thread_id": d["thread_id"], "device_id": "FJ-01"}, headers=H)
d = r.json()["data"]
print(r.status_code, "status:", d["status"], "| %.1fs" % (time.time() - t0), "| timings:", d["timings"])
print("summary:", d["payload"]["card"]["summary"])

print("\n=== 4) 确认 -> 报告 ===")
r = client.post("/diagnosis/review", json={"thread_id": d["thread_id"], "decision": "confirm"}, headers=H)
d = r.json()["data"]
print(r.status_code, "status:", d["status"], "| report_id:", d["report_id"])

print("\n=== 5) 取报告 ===")
r = client.get("/diagnosis/report/" + d["report_id"], headers=H)
rep = r.json()["data"]
print(r.status_code, "| 字数:", len(rep["content"]), "| 根因:", rep["record"]["root_cause"]["name"])
print("报告前 6 行:")
print("\n".join(rep["content"].split("\n")[:6]))

print("\n=== 6) 未授权访问 ===")
r = client.get("/diagnosis/history")
print(r.status_code, r.json()["code"], r.json()["message"])
