# -*- coding: utf-8 -*-
"""A2 检索验证：4 个演示 query。"""
from packages.rag.retriever import hybrid_search

CASES = [
    ("FJ-01 最近振动一直往上涨，是什么原因？", "FJ-01"),
    ("FJ-01 今天振动突然跳起来了", "FJ-01"),
    ("3 号机瓦温有点高，帮我看看", "FJ-03"),
    ("FJ-02 现在运行正常吗", "FJ-02"),
]
for q, dev in CASES:
    chunks, trace = hybrid_search(q, device_id=dev, top_p=5)
    print("=" * 90)
    print(f"Q: {q}  (device={dev})")
    print("  steps:", " | ".join(trace.steps), "| relaxed:", trace.relaxed_to_global,
          "| degraded:", trace.degraded)
    for c in chunks:
        print(f"  [{c.rerank_score if c.rerank_score is not None else '-'}] {c.locator} | {c.device_id} {c.doc_type} | {c.text[:52].replace(chr(10),' ')}")
