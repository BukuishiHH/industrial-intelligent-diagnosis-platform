# -*- coding: utf-8 -*-
"""构建 A2 检索索引（向量 + BM25）。用法：python scripts/build_index.py [--keep]"""
import argparse
import sys
import io


from packages.rag.index import build_index
from packages.rag.embedding import health

ap = argparse.ArgumentParser()
ap.add_argument("--keep", action="store_true", help="不重置已有向量集合（增量追加）")
args = ap.parse_args()

ok, msg = health()
print("embedding service:", ok, msg)
if not ok:
    print("!! 请先在 WSL2 启动 bge 模型服务（见 docs/环境与启动说明.md）")
    sys.exit(1)

meta = build_index(rebuild=not args.keep)
print("索引构建完成：")
for k, v in meta.items():
    print(f"  {k}: {v}")
