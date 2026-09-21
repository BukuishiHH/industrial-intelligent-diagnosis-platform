# -*- coding: utf-8 -*-
"""稠密向量客户端：调用 WSL2 内 SGLang 提供的 OpenAI 兼容 embedding 服务。

模型：BAAI/bge-large-zh-v1.5（1024 维，与 .env 的 DIMENSION 一致）
服务：WSL2 Ubuntu 内启动，Windows 侧经 localhost 转发访问（默认 http://localhost:30000/v1）

注意：
- **bge-v1.5 系列不需要 query instruction**（加指令反而略掉点），query 与 passage 同样编码。
- 服务未启动时抛出 EmbeddingUnavailable，由 A2 决定是否降级（不静默返回错误向量）。
"""
from __future__ import annotations

import os
from functools import lru_cache

from openai import OpenAI

from packages.core.config import settings

DEFAULT_MODEL_HINT = "bge-large-zh-v1.5"
# bge-large-zh-v1.5 的 max context = 512 token；超限服务端直接 400。
# 切块应保证 <=400 字，这里再做一次兜底截断（正常流程不应触发）。
MAX_EMBED_CHARS = int(os.getenv("EMBEDDING_MAX_CHARS", "420"))


class EmbeddingUnavailable(RuntimeError):
    """embedding 服务不可用（未启动 / 端口不通 / 模型未加载）。"""


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    return OpenAI(
        base_url=settings.EMBEDDING_BASE_URL,
        api_key=settings.EMBEDDING_API_KEY or "not-needed",
        timeout=float(os.getenv("EMBEDDING_TIMEOUT", "30")),
    )


@lru_cache(maxsize=1)
def service_model_id() -> str:
    """服务端真实模型 id：优先 .env 的 EMBEDDING_MODEL，否则向服务查询。"""
    if settings.EMBEDDING_MODEL:
        return settings.EMBEDDING_MODEL
    try:
        models = _client().models.list()
    except Exception as exc:                       # 服务未启动
        raise EmbeddingUnavailable(
            f"无法连接 embedding 服务 {settings.EMBEDDING_BASE_URL}：{exc}. "
            "请先在 WSL2 Ubuntu 中启动 bge 模型服务（见 docs/环境与启动说明.md）"
        ) from exc
    ids = [m.id for m in getattr(models, "data", [])]
    if not ids:
        raise EmbeddingUnavailable("embedding 服务未返回任何模型")
    return ids[0]


def _cosine(a: list[float], b: list[float]) -> float:
    import math

    s = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return s / (na * nb) if na and nb else 0.0


def quality_check() -> tuple[bool, str]:
    """检测服务是否返回**有效的语义向量**。

    只判断"能连上 + 维度对"是不够的：若服务未以 embedding 模式正确加载，
    会返回与输入无关的随机向量（表现为：同一文本两次请求的相似度远小于 1，
    或任意两段无关文本的相似度接近 1）。用这类向量建索引，稠密检索等同噪声。
    """
    probe = "轴承温度过高需要停机检修"
    try:
        first = embed_texts([probe])[0]
        second = embed_texts([probe])[0]
        unrelated = embed_texts(["今天天气不错适合出门散步"])[0]
    except Exception as exc:                       # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"

    same = _cosine(first, second)
    other = _cosine(first, unrelated)
    if same < 0.99:
        return False, (f"向量不确定（同一文本两次请求相似度仅 {same:.3f}，应 ≈1.0），"
                       f"服务返回的可能是随机向量；请检查 WSL2 启动参数（--is-embedding）与服务日志")
    if other > 0.8:
        return False, (f"向量区分度不足（无关文本相似度 {other:.3f}，应 <0.8），"
                       f"服务可能未按 embedding 模式加载")
    return True, f"OK（自一致 {same:.3f}，区分度 {other:.3f}）"


def health() -> tuple[bool, str]:
    """返回 (是否可用, 说明)，供启动自检与演示前检查使用。"""
    try:
        model_id = service_model_id()
        vec = embed_texts(["health check"])[0]
        if len(vec) != settings.EMBEDDING_DIM:
            return False, f"维度不匹配：服务返回 {len(vec)}，配置为 {settings.EMBEDDING_DIM}"
        ok_quality, quality_msg = quality_check()
        if not ok_quality:
            return False, quality_msg
        return True, f"OK（model={model_id.split('/')[-1]}，dim={len(vec)}，{quality_msg}）"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def embed_texts(texts: list[str], batch_size: int = 16) -> list[list[float]]:
    """批量编码；空输入返回空列表。"""
    if not texts:
        return []
    model_id = service_model_id()
    vectors: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = []
        for t in texts[i:i + batch_size]:
            t = t.strip() or " "
            if len(t) > MAX_EMBED_CHARS:          # 兜底：防止超出模型上下文被服务端拒绝
                t = t[:MAX_EMBED_CHARS]
            batch.append(t)
        try:
            resp = _client().embeddings.create(model=model_id, input=batch)
        except Exception as exc:
            raise EmbeddingUnavailable(f"embedding 调用失败：{exc}") from exc
        ordered = sorted(resp.data, key=lambda d: d.index)
        vectors.extend([list(d.embedding) for d in ordered])
    return vectors


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
