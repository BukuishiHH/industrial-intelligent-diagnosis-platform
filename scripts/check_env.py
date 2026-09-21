# -*- coding: utf-8 -*-
import importlib.util as u, sys, io
print("python:", sys.version.split()[0])
for m in ["openai","fastapi","uvicorn","pydantic_settings","docx","pymysql","jieba","langgraph","chromadb"]:
    try: ok = u.find_spec(m) is not None
    except Exception: ok = False
    print(("OK   " if ok else "--   ") + m)
import pandas, numpy, pydantic
print("pandas", pandas.__version__, "| numpy", numpy.__version__, "| pydantic", pydantic.VERSION)

print("--- embedding ---")
from packages.rag import embedding
ok, msg = embedding.health()
print("health:", ok, msg)

if ok:
    import math
    q = embedding.embed_query("FJ-01 驱动端振动持续上升是什么原因")
    docs = ["叶轮积灰结垢引起转子不平衡，1 倍频振动上升", "联轴器膜片疲劳裂纹，2 倍频振动增大",
            "油冷却器水侧结垢，供油温度升高引起瓦温上升", "电机空冷器翅片堵塞，绕组温度报警"]
    vs = embedding.embed_texts(docs)
    def cos(a,b):
        s=sum(x*y for x,y in zip(a,b)); na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(x*x for x in b)); return s/(na*nb)
    for d, v in zip(docs, vs):
        print(f"  {cos(q,v):.4f}  {d[:24]}")

print("--- embedding 向量质量 ---")
# 仅"能连上"不够：服务若未以 embedding 模式启动，会返回高度相似的退化向量，
# 稠密检索将退化为噪声（表现为任意两段文本相似度都接近 1）。
import math as _math
from packages.rag import embedding as _emb

def _cos(a, b):
    s = sum(x * y for x, y in zip(a, b))
    na = _math.sqrt(sum(x * x for x in a)); nb = _math.sqrt(sum(x * x for x in b))
    return s / (na * nb) if na and nb else 0.0

_probe = _emb.embed_texts(["轴承温度过高需要停机检修", "今天天气不错适合出门散步"])
_quality = _cos(_probe[0], _probe[1])
_ok_quality = _quality < 0.8
print(f"  无关文本相似度 {_quality:.4f}（期望 < 0.8）：" + ("正常" if _ok_quality else "**异常**"))
if not _ok_quality:
    print("  !! 向量服务返回退化向量：请确认 WSL2 启动命令带 --is-embedding，并查看服务日志")

print("--- 传感器数据可用性 ---")
# 只做"数据是否就绪"的检查（数据集会随演示重跑而更新，不能用固定日期断言）；
# 阈值/趋势规则的具体断言见 scripts/check_a3_digest.py
from packages.agents.a3_data import load_sensor_frame, resolve_data_path
_data_path = resolve_data_path()
_frame = load_sensor_frame()
print(f"  默认数据集: {_data_path.name}")
print(f"  行数 {len(_frame)} | 时间范围 {_frame['timestamp'].min()} ~ {_frame['timestamp'].max()}")
print(f"  覆盖设备: {sorted(_frame['device_id'].unique())} | 测点: {[c for c in _frame.columns if c not in ('timestamp', 'device_id')]}")

print("--- MySQL 与 checkpoint ---")
from packages.service.persistence import db_health, last_error
ok_db, msg_db = db_health()
print("database:", ok_db, msg_db)
from packages.service.diagnosis_service import build_checkpointer
_, backend = build_checkpointer()
print("checkpoint backend:", backend)
if last_error():
    print("最近一次持久化错误:", last_error())

print("--- A1 LLM 通道 ---")
from packages.agents.a1_intent import recognize
r, ch = recognize("FJ-01 最近振动一直往上涨，什么原因？")
print(f"  channel={ch} intent={r.intent} device={r.device_id} sensors={r.sensor_hint} conf={r.confidence}")
