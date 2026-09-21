# -*- coding: utf-8 -*-
"""A2 索引构建：文档 -> 切块 -> 向量（Chroma）+ 稀疏（BM25）。

索引产物可复用，只有在文档或切块参数变化时才需要重建（scripts/build_index.py）。
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from packages.core.config import BASE_DIR
from packages.rag.bm25 import BM25Index
from packages.rag.chunking import Chunk, load_all_chunks
from packages.rag.embedding import embed_texts
from packages.rag.store import get_store

INDEX_DIR = BASE_DIR / "data" / "index"
BM25_PATH = INDEX_DIR / "bm25.pkl"
META_PATH = INDEX_DIR / "index_meta.json"
EMBED_BATCH = 16


def chunk_to_metadata(chunk: Chunk) -> dict:
    """Chroma metadata 只支持标量；None 用空串代替。"""
    return {
        "doc_id": chunk.doc_id,
        "doc_type": chunk.doc_type,
        "doc_type_cn": chunk.meta.get("doc_type_cn", ""),
        "device_id": chunk.device_id,
        "section": chunk.section or "",
        "case_no": chunk.case_no or "",
        "locator": chunk.locator,
        "doc_file": chunk.meta.get("doc_file", ""),
        "title": chunk.meta.get("title", ""),
    }


def build_index(raw_dir: str | Path | None = None, rebuild: bool = True,
                chunk_size: int = 500, overlap: int = 50) -> dict:
    """构建/重建索引，返回统计信息。"""
    started = time.time()
    chunks = load_all_chunks(raw_dir or (BASE_DIR / "data" / "raw_docs"),
                             chunk_size=chunk_size, overlap=overlap)
    if not chunks:
        raise RuntimeError("未解析到任何文档块，请检查 data/raw_docs 下的文档")

    store = get_store()
    if rebuild:
        store.reset()

    texts = [c.text for c in chunks]
    vectors: list[list[float]] = []
    for i in range(0, len(texts), EMBED_BATCH):
        vectors.extend(embed_texts(texts[i:i + EMBED_BATCH], batch_size=EMBED_BATCH))

    store.add(
        ids=[c.chunk_id for c in chunks],
        embeddings=vectors,
        documents=texts,
        metadatas=[chunk_to_metadata(c) for c in chunks],
    )

    bm25 = BM25Index().build([(c.chunk_id, c.text) for c in chunks])
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    bm25.save(BM25_PATH)

    meta = {
        "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "vector_backend": os.getenv("VECTOR_STORE", "memory"),
        "chunks": len(chunks),
        "vectors": store.count(),
        "dim": len(vectors[0]) if vectors else 0,
        "chunk_size": chunk_size,
        "overlap": overlap,
        "by_type": {t: sum(1 for c in chunks if c.doc_type == t) for t in set(c.doc_type for c in chunks)},
        "by_device": {d: sum(1 for c in chunks if c.device_id == d) for d in set(c.device_id for c in chunks)},
        "elapsed_seconds": round(time.time() - started, 1),
    }
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def load_bm25() -> BM25Index:
    if not BM25_PATH.exists():
        raise FileNotFoundError(f"未找到 BM25 索引 {BM25_PATH}，请先运行 scripts/build_index.py")
    return BM25Index.load(BM25_PATH)


def load_chunk_map() -> dict[str, Chunk]:
    """chunk_id -> Chunk（检索结果需要正文与元数据）。"""
    chunks = load_all_chunks(BASE_DIR / "data" / "raw_docs")
    return {c.chunk_id: c for c in chunks}


def index_meta() -> dict:
    if not META_PATH.exists():
        return {}
    return json.loads(META_PATH.read_text(encoding="utf-8"))
