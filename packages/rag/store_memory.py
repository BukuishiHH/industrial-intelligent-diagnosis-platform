# -*- coding: utf-8 -*-
"""内存向量库（numpy）——与 VectorStore 接口一致的等价替代。

存在意义：ChromaDB 在部分 Windows + Python 3.12 组合下原生扩展会直接崩溃（进程级，
无法 try/except 捕获），此时可用 VECTOR_STORE=memory 切换，功能与检索结果等价。
数据规模在万级 chunk 以内时，numpy 矩阵乘法的检索速度优于向量数据库。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from packages.core.config import BASE_DIR

DEFAULT_PATH = BASE_DIR / "data" / "index" / "memory"


class MemoryVectorStore:
    def __init__(self, path: str | Path = DEFAULT_PATH, collection: str = "iip_docs"):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.name = collection
        self.vectors_path = self.path / f"{collection}.npy"
        self.meta_path = self.path / f"{collection}.jsonl"
        self.ids: list[str] = []
        self.documents: list[str] = []
        self.metadatas: list[dict[str, Any]] = []
        self.matrix: np.ndarray | None = None
        self._load()

    def _load(self) -> None:
        if not (self.vectors_path.exists() and self.meta_path.exists()):
            return
        self.matrix = np.load(self.vectors_path)
        for line in self.meta_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            self.ids.append(row["id"])
            self.documents.append(row["document"])
            self.metadatas.append(row["metadata"])

    def _persist(self) -> None:
        if self.matrix is not None:
            np.save(self.vectors_path, self.matrix)
        with open(self.meta_path, "w", encoding="utf-8") as fh:
            for cid, doc, meta in zip(self.ids, self.documents, self.metadatas):
                fh.write(json.dumps({"id": cid, "document": doc, "metadata": meta},
                                    ensure_ascii=False) + "\n")

    def count(self) -> int:
        return len(self.ids)

    def reset(self) -> None:
        self.ids, self.documents, self.metadatas, self.matrix = [], [], [], None
        for p in (self.vectors_path, self.meta_path):
            if p.exists():
                p.unlink()

    def add(self, ids: Sequence[str], embeddings: Sequence[Sequence[float]],
            documents: Sequence[str], metadatas: Sequence[dict[str, Any]]) -> None:
        arr = np.asarray(embeddings, dtype=np.float32)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        arr = arr / np.clip(norms, 1e-12, None)              # 归一化 -> 内积即余弦
        self.matrix = arr if self.matrix is None else np.vstack([self.matrix, arr])
        self.ids.extend(ids)
        self.documents.extend(documents)
        self.metadatas.extend(metadatas)
        self._persist()

    def query(self, embedding: Sequence[float], n_results: int = 20,
              where: dict[str, Any] | None = None) -> list[tuple[str, float]]:
        if self.matrix is None or not self.ids:
            return []
        q = np.asarray(embedding, dtype=np.float32)
        q = q / max(float(np.linalg.norm(q)), 1e-12)
        sims = self.matrix @ q
        idx = list(range(len(self.ids)))
        if where:
            idx = [i for i in idx
                   if all(self.metadatas[i].get(k) == v for k, v in where.items())]
        idx.sort(key=lambda i: -float(sims[i]))
        return [(self.ids[i], float(sims[i])) for i in idx[:n_results]]

    def get(self, chunk_id: str) -> dict[str, Any] | None:
        if chunk_id not in self.ids:
            return None
        i = self.ids.index(chunk_id)
        return {"id": chunk_id, "document": self.documents[i], "metadata": self.metadatas[i]}

    def fetch(self, chunk_ids: Sequence[str]) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for cid in chunk_ids:
            row = self.get(cid)
            if row:
                out[cid] = row
        return out
