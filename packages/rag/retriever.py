# -*- coding: utf-8 -*-
"""A2 检索节点：混合检索（稠密 + 稀疏）→ RRF 融合 → 重排 → top-p。

决策依据：
- 稠密 bge-large-zh-v1.5 走 WSL2 内的 embedding 服务；稀疏为内存 BM25（jieba 分词）。
- RRF(k=60) 免调权重，dense/sparse 各取 top-20 后融合。
- 设备优先：先按 device_id 过滤，命中不足再放宽全库并标注（决策 D8）。
- 重排：LLM 重排（决策 P1），失败自动退化为 RRF 顺序且不打断链路。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

from packages.rag.bm25 import BM25Index, tokenize
from packages.rag.embedding import embed_query
from packages.rag.index import load_bm25
from packages.rag.rerank import Candidate, rerank as rerank_candidates
from packages.rag.store import get_store
from packages.schemas.diagnosis import RetrievedChunk

RRF_K = 60
DEFAULT_TOP_P = 5


@dataclass
class SearchTrace:
    dense_hits: int = 0
    sparse_hits: int = 0
    fused: int = 0
    device_filter: str | None = None
    relaxed_to_global: bool = False
    rerank_backend: str = "none"
    degraded: bool = False
    note: str = ""
    steps: list[str] = field(default_factory=list)


@lru_cache(maxsize=1)
def _store():
    return get_store()


@lru_cache(maxsize=1)
def _bm25() -> BM25Index:
    return load_bm25()


def _rrf(rank_lists: dict[str, list[str]], k: int = RRF_K) -> dict[str, float]:
    scores: dict[str, float] = {}
    for _, ids in rank_lists.items():
        for rank, cid in enumerate(ids, start=1):
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
    return scores


def _to_chunk(cid: str, row: dict, score: float, rerank_score: float | None = None) -> RetrievedChunk:
    meta = row.get("metadata") or {}
    return RetrievedChunk(
        chunk_id=cid,
        text=row.get("document") or "",
        score=round(score, 6),
        rerank_score=rerank_score,
        doc_id=meta.get("doc_id"),
        doc_type=meta.get("doc_type"),
        device_id=meta.get("device_id"),
        section=meta.get("section") or None,
        page=meta.get("page") or None,
        case_no=meta.get("case_no") or None,
        locator=meta.get("locator"),
    )


def _candidates(query: str, device_id: str | None, top_k_dense: int, top_k_sparse: int,
                trace: SearchTrace) -> list[tuple[str, float]]:
    store = _store()
    where = {"device_id": device_id} if device_id else None
    dense: list[tuple[str, float]] = []
    try:
        dense = store.query(embed_query(query), n_results=top_k_dense, where=where)
        trace.steps.append(f"稠密检索：{len(dense)} 条" + (f"（设备过滤 {device_id}）" if device_id else ""))
    except Exception as exc:                      # noqa: BLE001
        # 向量服务不可用（如 WSL2 模型服务未启动）时不阻断诊断：退化为纯 BM25 稀疏检索
        trace.degraded = True
        trace.note = "稠密检索不可用，已退化为纯 BM25 稀疏检索"
        trace.steps.append(f"稠密检索：跳过（{type(exc).__name__}）")
    trace.dense_hits = len(dense)

    sparse_all = _bm25().search(query, top_k=top_k_sparse * 4)
    sparse = [(cid, s) for cid, s in sparse_all
              if device_id is None or (_store().fetch([cid]).get(cid, {}).get("metadata", {}).get("device_id") == device_id)]
    sparse = sparse[:top_k_sparse]
    trace.sparse_hits = len(sparse)
    trace.steps.append(f"稀疏检索（BM25）：{len(sparse)} 条")

    fused = _rrf({"dense": [c for c, _ in dense], "sparse": [c for c, _ in sparse]})
    ordered = sorted(fused.items(), key=lambda x: -x[1])
    trace.fused = len(ordered)
    return ordered


def hybrid_search(
    query: str,
    device_id: str | None = None,
    top_p: int = DEFAULT_TOP_P,
    top_k_dense: int = 20,
    top_k_sparse: int = 20,
    use_rerank: bool = True,
) -> tuple[list[RetrievedChunk], SearchTrace]:
    trace = SearchTrace(device_filter=device_id)
    store = _store()
    ordered = _candidates(query, device_id, top_k_dense, top_k_sparse, trace)

    # 设备过滤命中不足 -> 放宽全库（保留设备标注，供 A4 判断跨设备经验）
    if device_id and len(ordered) < top_p:
        trace.relaxed_to_global = True
        trace.note = f"{device_id} 本设备命中不足 {top_p} 条，已放宽到全库检索"
        extra = _candidates(query, None, top_k_dense, top_k_sparse, SearchTrace())
        merged = dict(ordered)
        for cid, score in extra:
            merged.setdefault(cid, score)
        ordered = sorted(merged.items(), key=lambda x: -x[1])

    if not ordered:
        trace.degraded = True
        trace.note = (trace.note + "；" if trace.note else "") + "检索无结果"
        return [], trace

    pool = [cid for cid, _ in ordered[:max(top_k_dense, top_p)]]
    rows = store.fetch(pool)
    chunks = [_to_chunk(cid, rows.get(cid, {}), score) for cid, score in ordered[:len(pool)] if cid in rows]

    if use_rerank and len(chunks) > 1:
        cands = [Candidate(chunk_id=c.chunk_id, text=c.text, score=c.score,
                           metadata={"locator": c.locator or "", "doc_id": c.doc_id or ""}) for c in chunks]
        result = rerank_candidates(query, cands, top_p=top_p)
        by_id = {c.chunk_id: c for c in chunks}
        reranked: list[RetrievedChunk] = []
        for cand in result.items:
            chunk = by_id.get(cand.chunk_id)
            if chunk:
                chunk.rerank_score = cand.rerank_score
                reranked.append(chunk)
        chunks = reranked
        trace.rerank_backend = result.backend
        trace.degraded = trace.degraded or result.degraded
        if result.note:
            trace.note = (trace.note + "；" if trace.note else "") + result.note
        trace.steps.append(f"重排（{result.backend}）：{len(chunks)} 条")
    else:
        chunks = chunks[:top_p]

    trace.steps.append(f"最终返回 {len(chunks)} 条")
    return chunks, trace
