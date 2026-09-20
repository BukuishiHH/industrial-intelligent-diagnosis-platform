# -*- coding: utf-8 -*-
"""向量库封装（ChromaDB 持久化）。

选型依据：MySQL 存业务数据 + ChromaDB 存向量 + 内存 BM25（设计决策 D7），不引入 ES/PG。
embedding 由 WSL2 内的 bge 服务提供，因此这里只负责存取，不使用 Chroma 自带的 embedding function。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Sequence

from packages.core.config import BASE_DIR

DEFAULT_PATH = BASE_DIR / "data" / "index" / "chroma"
COLLECTION = "iip_docs"


class VectorStore:
    def __init__(self, path: str | Path = DEFAULT_PATH, collection: str = COLLECTION):
        # 延迟导入：chromadb 部分版本在 Windows 上原生崩溃时，memory 后端仍可正常使用
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(self.path),
            settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
        )
        self.name = collection
        self.collection = self.client.get_or_create_collection(
            name=collection, metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        return int(self.collection.count())

    def reset(self) -> None:
        try:
            self.client.delete_collection(self.name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=self.name, metadata={"hnsw:space": "cosine"},
        )

    def add(self, ids: Sequence[str], embeddings: Sequence[Sequence[float]],
            documents: Sequence[str], metadatas: Sequence[dict[str, Any]]) -> None:
        self.collection.add(ids=list(ids), embeddings=[list(e) for e in embeddings],
                            documents=list(documents), metadatas=list(metadatas))

    def query(self, embedding: Sequence[float], n_results: int = 20,
              where: dict[str, Any] | None = None) -> list[tuple[str, float]]:
        """返回 [(chunk_id, similarity)]，similarity = 1 - cosine_distance。"""
        res = self.collection.query(
            query_embeddings=[list(embedding)],
            n_results=n_results,
            where=where or None,
            include=["distances"],
        )
        ids = (res.get("ids") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        return [(cid, float(1.0 - d)) for cid, d in zip(ids, dists)]


    def fetch(self, chunk_ids: Sequence[str]) -> dict[str, dict[str, Any]]:
        if not chunk_ids:
            return {}
        res = self.collection.get(ids=list(chunk_ids), include=["documents", "metadatas"])
        out: dict[str, dict[str, Any]] = {}
        for cid, doc, meta in zip(res.get("ids", []), res.get("documents", []), res.get("metadatas", [])):
            out[cid] = {"id": cid, "document": doc, "metadata": meta}
        return out


def get_store(prefer: str | None = None):
    """向量库工厂：VECTOR_STORE=chroma|memory（默认 chroma）。

    memory 后端见 store_memory.py —— 当 ChromaDB 在本机原生崩溃（进程级，无法捕获）时切换。
    """
    backend = (prefer or os.getenv("VECTOR_STORE", "memory")).lower()
    if backend == "memory":
        from packages.rag.store_memory import MemoryVectorStore
        return MemoryVectorStore()
    return VectorStore()
