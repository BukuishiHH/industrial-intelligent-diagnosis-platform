# -*- coding: utf-8 -*-
import sys, io
from collections import Counter
from packages.rag.chunking import load_all_chunks
chunks = load_all_chunks("data/raw_docs", chunk_size=500, overlap=50)
print("总块数:", len(chunks))
print("按文档类型:", dict(Counter(c.doc_type for c in chunks)))
print("按设备:", dict(Counter(c.device_id for c in chunks)))
print("含案例号的块:", sum(1 for c in chunks if c.case_no))
print()
for c in chunks[:2] + [c for c in chunks if c.case_no == "案例1" and c.device_id == "FJ-01"][:2]:
    print(f"--- {c.chunk_id} | {c.locator} | device={c.device_id} type={c.doc_type} len={len(c.text)}")
    print(c.text[:260].replace("\n", " ⏎ "))
    print()
from packages.rag.bm25 import BM25Index
idx = BM25Index().build([(c.chunk_id, c.text) for c in chunks])
for q in ["FJ-01 振动持续上升 什么原因", "瓦温高 油冷却器", "碰磨 振动突增"]:
    print(f"query={q!r} ->", [(cid, round(s, 2)) for cid, s in idx.search(q, top_k=3)])
