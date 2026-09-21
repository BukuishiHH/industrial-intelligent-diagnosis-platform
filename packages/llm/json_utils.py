# -*- coding: utf-8 -*-
"""LLM 结构化输出的解析容错。

大模型偶尔会返回带 markdown 代码块围栏、前后缀说明、或被 max_tokens 截断的内容。
这里提供统一的宽松解析：直接解析 -> 去围栏 -> 截取首个平衡的 JSON 对象。
"""
from __future__ import annotations

import json
import re

# 匹配 markdown 代码块围栏（用 \x60 写反引号，避免源码里出现连续反引号）
_RE_FENCE = re.compile(r"\x60\x60\x60(?:json)?\s*(.+?)\s*\x60\x60\x60", re.S)


def parse_json_response(text: str) -> dict:
    """尽力把模型输出解析成 dict，失败抛 ValueError。"""
    if not text or not text.strip():
        raise ValueError("模型返回空内容")

    candidates: list[str] = [text.strip()]
    fenced = _RE_FENCE.search(text)
    if fenced:
        candidates.append(fenced.group(1).strip())

    start = text.find("{")
    if start >= 0:
        depth, in_str, escape = 0, False, False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if escape:
                    escape = False
                elif ch == chr(92):
                    escape = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidates.append(text[start:i + 1])
                    break

    for candidate in candidates:
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            continue
    raise ValueError("无法从模型输出中解析出 JSON 对象（可能被截断）：" + text[:120])
