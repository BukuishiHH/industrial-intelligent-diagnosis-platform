# -*- coding: utf-8 -*-
"""稀疏检索：jieba 分词 + 自实现 BM25（不引入 ES / rank_bm25 依赖）。

设计说明：5091 量级的 chunk 用内存倒排完全够用，且与 ChromaDB 并列构成混合检索的稀疏路。
"""
from __future__ import annotations

import math
import pickle
import re
from collections import Counter
from pathlib import Path

import jieba

# 工业术语与设备位号必须整体成词，否则会被切碎导致召回下降
USER_WORDS = [
    "FJ-01", "FJ-02", "FJ-03", "引风机", "离心引风机", "叶轮", "积灰", "结垢", "转子不平衡",
    "联轴器", "膜片", "柱销", "轴承", "瓦温", "轴瓦", "乌金", "巴氏合金", "油压", "供油压力",
    "稀油站", "喘振", "碰磨", "对中", "动平衡", "迷宫密封", "调压阀", "滤芯", "滤油器",
    "油冷却器", "空冷器", "导叶", "膨胀节", "地脚螺栓", "减振垫", "驱动端", "非驱动端",
    "前轴承", "后轴承", "振动", "转速", "电流", "报警", "跳机", "跳车", "联锁", "检修",
    "试车", "验收", "绕组", "匝间短路", "变频器", "风道", "机壳", "叶片", "主轴", "轴承座",
]
for _w in USER_WORDS:
    jieba.add_word(_w)

STOPWORDS = set("的 了 在 是 和 与 及 对 为 以 上 下 中 有 无 不 也 都 就 而 被 把 从 到 按 等 该 其 之 或 并 由 于 内 外 时 后 前 个 条 项 应 可 需 要 进行 发生 出现 情况 要求 规定 相关 采用 以及".split())
_RE_TOKEN = re.compile(r"[A-Za-z0-9\-\.]+")


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for tok in jieba.lcut(text or "", cut_all=False):
        tok = tok.strip().lower()
        if not tok or tok in STOPWORDS or len(tok) == 1 and not _RE_TOKEN.match(tok):
            continue
        if len(tok) == 1 and not _RE_TOKEN.match(tok):
            continue
        tokens.append(tok)
    return tokens


class BM25Index:
    """经典 BM25（k1=1.5, b=0.75）。"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.chunk_ids: list[str] = []
        self.doc_tokens: list[list[str]] = []
        self.doc_len: list[int] = []
        self.avg_len: float = 0.0
        self.tf: list[Counter] = []
        self.df: Counter = Counter()
        self.n_docs: int = 0

    def build(self, items: list[tuple[str, str]]) -> "BM25Index":
        """items: [(chunk_id, text)]"""
        self.chunk_ids = [cid for cid, _ in items]
        self.doc_tokens = [tokenize(text) for _, text in items]
        self.doc_len = [len(t) for t in self.doc_tokens]
        self.n_docs = len(items)
        self.avg_len = (sum(self.doc_len) / self.n_docs) if self.n_docs else 0.0
        self.tf = [Counter(t) for t in self.doc_tokens]
        self.df = Counter()
        for tokens in self.doc_tokens:
            self.df.update(set(tokens))
        return self

    def _idf(self, term: str) -> float:
        df = self.df.get(term, 0)
        return math.log(1 + (self.n_docs - df + 0.5) / (df + 0.5))

    def search(self, query: str, top_k: int = 20) -> list[tuple[str, float]]:
        if not self.n_docs:
            return []
        scores = [0.0] * self.n_docs
        for term in tokenize(query):
            idf = self._idf(term)
            if idf <= 0:
                continue
            for i, tf in enumerate(self.tf):
                f = tf.get(term)
                if not f:
                    continue
                denom = f + self.k1 * (1 - self.b + self.b * self.doc_len[i] / (self.avg_len or 1))
                scores[i] += idf * f * (self.k1 + 1) / denom
        ranked = sorted(((self.chunk_ids[i], s) for i, s in enumerate(scores) if s > 0),
                        key=lambda x: -x[1])
        return ranked[:top_k]

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as fh:
            pickle.dump(self, fh)

    @staticmethod
    def load(path: str | Path) -> "BM25Index":
        with open(path, "rb") as fh:
            return pickle.load(fh)
