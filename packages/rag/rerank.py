# -*- coding: utf-8 -*-
"""A2 知识检索链路的重排（Rerank）模块。

设计依据：docs/业务场景设计_设备检修诊断.md §4.1（决策 P1）

- 当前实现 `backend="llm"`：用 deepseek-flash 对 RRF 融合后的候选做相关性重排。
  选它的原因：本地只有 `BAAI/bge-large-zh-v1.5`（双塔嵌入模型，不能当 cross-encoder），
  而 `BAAI/bge-reranker-v2-m3` 尚未下载。
- 预留实现 `backend="bge"`：本地 bge-reranker 交叉编码器。模型下载完成后把
  `RERANK_BACKEND` 环境变量改成 `bge`（或调用时传 backend="bge"）即可切换，调用方无需改动。
- 失败降级：LLM 超时/解析失败时退回 RRF 原始顺序，返回 `degraded=True`，绝不抛异常打断诊断链路。
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Sequence

# 单条候选送入 LLM 的最大字符数（控制 token 与延迟）
MAX_CHARS_PER_CANDIDATE = 200
# 送入重排的候选上限（直接影响 LLM 重排耗时）
MAX_CANDIDATES = 8
DEFAULT_TOP_P = 5


@dataclass
class Candidate:
    """一条候选知识片段（来自 A2 的 dense/sparse 召回 + RRF 融合）。"""

    chunk_id: str
    text: str
    score: float = 0.0                       # 融合分数（RRF）
    metadata: dict[str, Any] = field(default_factory=dict)
    rerank_score: float | None = None        # 重排分数，未重排时为 None


@dataclass
class RerankResult:
    items: list[Candidate]
    backend: str
    degraded: bool = False
    note: str = ""


_LLM_SYSTEM_PROMPT = """你是工业设备故障诊断系统的检索结果重排器。
用户会给你一条查询和一个候选片段列表，请按"对回答该查询的有用程度"从高到低排序。
判定要点：是否直接描述了查询涉及的设备部件、故障现象、原因或处置措施；跨设备/跨机型的泛泛内容应靠后。
只输出 JSON，不要解释，格式为按相关性从高到低排列的候选编号数组：
{"ranking": [3, 1, 5, 2, 4]}
必须包含每个候选编号且不重复。不要输出分数或理由。"""


def _build_user_prompt(query: str, candidates: Sequence[Candidate]) -> str:
    lines = [f"查询：{query}", "", "候选片段："]
    for i, c in enumerate(candidates, start=1):
        text = " ".join(c.text.split())[:MAX_CHARS_PER_CANDIDATE]
        locator = c.metadata.get("locator") or c.metadata.get("doc_id") or ""
        lines.append(f"[{i}] ({locator}) {text}")
    return "\n".join(lines)


def _rerank_by_llm(query: str, candidates: Sequence[Candidate], top_p: int) -> RerankResult:
    """用 deepseek-flash 做重排（决策 P1 路径 B）。"""
    from packages.core.config import settings          # 延迟导入，避免模块导入即依赖环境变量
    from packages.llm.client import client

    prompt = _build_user_prompt(query, candidates)
    # max_retries=0：重排是"锦上添花"，失败就退回 RRF 顺序，绝不因重试吃掉 60s 预算
    llm = client.with_options(timeout=float(os.getenv("RERANK_TIMEOUT", "12")), max_retries=0)
    try:
        resp = llm.chat.completions.create(
            model=settings.DEEPSEEK_MODEL_NAME,
            messages=[
                {"role": "system", "content": _LLM_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        payload = json.loads(resp.choices[0].message.content or "{}")
        ranking = payload.get("ranking") or []
    except Exception as exc:                            # 网络/解析/超时一律降级
        return _fallback(candidates, top_p, f"LLM 重排失败，已退回 RRF 顺序：{exc}")

    scored: list[tuple[float, int, Candidate]] = []
    seen: set[int] = set()
    for pos, item in enumerate(ranking):
        raw = item.get("index") if isinstance(item, dict) else item   # 兼容 [{"index":1}] 与 [1,3,2]
        try:
            idx = int(raw) - 1
        except (TypeError, ValueError):
            continue
        if idx < 0 or idx >= len(candidates) or idx in seen:
            continue
        seen.add(idx)
        # 数组顺序即相关性顺序，用倒数位置作为分数（仅用于排序展示）
        scored.append((float(len(ranking) - pos), idx, candidates[idx]))

    if not scored:
        return _fallback(candidates, top_p, "LLM 未返回可解析的 ranking，已退回 RRF 顺序")

    scored.sort(key=lambda t: (-t[0], t[1]))
    total = float(len(scored))
    scored = [((s + 1) / total, i, c) for s, i, c in scored]      # 归一到 0~1 便于展示
    ordered = [c for _, _, c in scored]
    for score, _, cand in scored:
        cand.rerank_score = score
    # LLM 漏掉的候选按 RRF 原顺序补在尾部，保证不丢召回
    ordered.extend(c for i, c in enumerate(candidates) if i not in seen)
    return RerankResult(items=ordered[:top_p], backend="llm")


def _rerank_by_bge(query: str, candidates: Sequence[Candidate], top_p: int) -> RerankResult:
    """本地 bge-reranker 交叉编码器（预留，模型下载完成后启用）。

    启用方式：下载 `BAAI/bge-reranker-v2-m3` 后将 `RERANK_BACKEND` 设为 `bge`。
    """
    try:
        from FlagEmbedding import FlagReranker      # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "backend='bge' 需要 FlagEmbedding 与本地 bge-reranker 模型；"
            "当前未安装/未下载，请继续使用 backend='llm'"
        ) from exc

    model_path = os.getenv("RERANK_MODEL_PATH", "BAAI/bge-reranker-v2-m3")
    reranker = FlagReranker(model_path, use_fp16=True)
    pairs = [[query, c.text] for c in candidates]
    scores = reranker.compute_score(pairs, normalize=True)
    if isinstance(scores, float):
        scores = [scores]
    for cand, score in zip(candidates, scores):
        cand.rerank_score = float(score)
    ordered = sorted(candidates, key=lambda c: c.rerank_score or 0.0, reverse=True)
    return RerankResult(items=ordered[:top_p], backend="bge")


def _fallback(candidates: Sequence[Candidate], top_p: int, note: str) -> RerankResult:
    return RerankResult(items=list(candidates[:top_p]), backend="none", degraded=True, note=note)


def rerank(
    query: str,
    candidates: Sequence[Candidate],
    top_p: int = DEFAULT_TOP_P,
    backend: str | None = None,
) -> RerankResult:
    """对 A2 召回结果重排，返回 top_p 条。

    :param query: 用户原始查询（不做改写）
    :param candidates: RRF 融合后的候选（建议 ≤ 20 条）
    :param top_p: 返回条数，默认 5
    :param backend: "llm" | "bge"，默认取环境变量 RERANK_BACKEND，再默认 "llm"
    """
    backend = (backend or os.getenv("RERANK_BACKEND") or "llm").lower()
    candidates = list(candidates)[:MAX_CANDIDATES]
    if not candidates:
        return RerankResult(items=[], backend=backend, note="无候选，跳过重排")

    if backend == "bge":
        try:
            return _rerank_by_bge(query, candidates, top_p)
        except RuntimeError as exc:
            result = _rerank_by_llm(query, candidates, top_p)
            result.note = f"bge 后端不可用（{exc}），已改用 LLM 重排"
            return result
    return _rerank_by_llm(query, candidates, top_p)
