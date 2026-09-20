# -*- coding: utf-8 -*-
"""文档解析与切块（A2 的第一段）。

要点：
- 27 份文档为 .docx（操作手册 / 维修手册 / 故障案例手册），按文件名识别设备与文档类型。
- **故障案例手册以"案例 N"为自然切块边界**（每个案例自洽：现象+原因+维修过程+预防），
  操作/维修手册按章节标题切块，超长块再按 CHUNK_SIZE/CHUNK_OVERLAP 细分。
- 每个 chunk 携带元数据：doc_id / doc_type / device_id / section / case_no / locator，
  用于 A2 的设备过滤与 A4 的证据溯源（locator 直接展示给用户）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
import zipfile
from pathlib import Path

from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

DOC_TYPE_MAP = [("故障案例手册", "case"), ("维修手册", "maintenance"), ("操作手册", "operation")]
DOC_TYPE_CN = {"case": "故障案例手册", "maintenance": "维修手册", "operation": "设备操作手册"}

_RE_DEVICE_IN_NAME = re.compile(r"(FJ-\d{2})")
_RE_CASE_TITLE = re.compile(r"^案例\s*(\d+)\s*[：:]\s*(.+)$")
_RE_SECTION_TITLE = re.compile(r"^(\d+(?:\.\d+)*)\s*(\S.{0,60})$")
_RE_APPENDIX = re.compile(r"^附录\s*\S*")
_RE_TOC_ITEM = re.compile(r"^(?:案例\s*\d+|附录|\d+(?:\.\d+)*)[^\n]{0,60}?\d+$")


@dataclass
class Chunk:
    chunk_id: str
    text: str
    doc_id: str
    doc_type: str
    device_id: str
    section: str | None = None
    case_no: str | None = None
    page: int | None = None
    locator: str = ""
    meta: dict = field(default_factory=dict)


# ---------------------------------------------------------------- 解析
def _iter_blocks(doc):
    """按文档顺序交替产出段落与表格（表格内容常含故障现象/原因/维修过程）。"""
    body = doc.element.body
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield "p", Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield "t", Table(child, doc)


def _table_to_text(table: Table) -> str:
    rows = []
    for row in table.rows:
        cells = [c.text.strip().replace("\n", " ") for c in row.cells]
        # 合并单元格会重复出现同一文本，去掉相邻重复
        deduped: list[str] = []
        for cell in cells:
            if not deduped or deduped[-1] != cell:
                deduped.append(cell)
        line = " | ".join([c for c in deduped if c])
        if line:
            rows.append(line)
    return "\n".join(rows)


def _text_lines_from_mht(path: Path) -> list[str]:
    """WPS 另存的 docx 会把正文放进 word/afchunk.mht（MHTML 分块），document.xml 只剩空壳。

    这类文件必须从 mht 里取 HTML 再转纯文本，否则整份文档会解析成 0 块。
    """
    import email
    import html as html_mod

    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith("afchunk.mht")]
        if not names:
            return []
        raw = zf.read(names[0])

    parts: list[str] = []
    for part in email.message_from_bytes(raw).walk():
        if part.get_content_type() not in ("text/html", "text/plain"):
            continue
        payload = part.get_payload(decode=True) or b""
        if payload:
            parts.append(payload.decode(part.get_content_charset() or "utf-8", "ignore"))
    if not parts:
        return []
    text = "\n".join(parts)
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<br[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"</(p|div|tr|h[1-6]|li)>", "\n", text, flags=re.I)
    text = re.sub(r"</t[dh]>", " | ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html_mod.unescape(text).replace("\xa0", " ").replace("\u3000", " ")
    return [ln.strip(" \t|") for ln in text.split("\n") if ln.strip(" \t|")]


def _classify(text: str) -> str:
    if _RE_CASE_TITLE.match(text) or _RE_SECTION_TITLE.match(text) or _RE_APPENDIX.match(text):
        return "title"
    if len(text) <= 40 and re.match(r"^(概述|目录|前言|说明)$", text):
        return "title"
    return "body"


def extract_blocks(path: Path) -> tuple[list[tuple[str, str]], dict]:
    """返回 (blocks, meta)。blocks 为 [("title"|"body", text)]。"""
    doc = Document(str(path))
    lines: list[str] = []
    for kind, item in _iter_blocks(doc):
        if kind == "t":
            text = _table_to_text(item)
            if text:
                lines.extend(text.split("\n"))
            continue
        text = (item.text or "").strip()
        if text:
            lines.append(text)

    if not lines:                                   # 空壳文档 -> 走 mht
        lines = _text_lines_from_mht(path)

    blocks: list[tuple[str, str]] = []
    in_toc = False
    for text in lines:
        if "TOC" in text or re.match(r"^目\s*录$", text):
            in_toc = True
            continue
        if in_toc:
            # 目录项形如 "案例1：xxx1" / "1.1 维修目的与适用范围1"
            if _RE_TOC_ITEM.match(text) or re.match(r"^(概述|附录).*\d+$", text):
                continue
            in_toc = False
        blocks.append((_classify(text), text))
    return blocks, {}


def meta_from_filename(path: Path) -> dict:
    name = path.stem
    device = _RE_DEVICE_IN_NAME.search(name)
    doc_type = next((v for k, v in DOC_TYPE_MAP if k in name), "other")
    prefix = f"{device.group(1).replace('-', '')}-{ {'case': 'GZ', 'maintenance': 'WX', 'operation': 'CZ'}.get(doc_type, 'XX') }" if device else name
    return {
        "doc_id": path.stem,
        "doc_short": prefix,
        "doc_type": doc_type,
        "device_id": device.group(1) if device else "GENERAL",
        "file": str(path),
    }


# ---------------------------------------------------------------- 切块
def _split_long(text: str, chunk_size: int, overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    parts, start = [], 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        parts.append(text[start:end])
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return parts


# bge-large-zh-v1.5 的上下文仅 512 token（约 420 汉字），切块必须留出安全余量，
# 否则 embedding 服务会直接返回 400。这也是 .env 里 CHUNK_SIZE 的有效上限。
MIN_GROUP_CHARS = 180      # 短于此长度的小节向后合并，避免产生大量碎片块
MAX_GROUP_CHARS = 400      # 合并上限，超过则不再并入


def _group_len(group: dict) -> int:
    return len(group["title"] or "") + sum(len(x) for x in group["lines"])


def _merge_short_groups(groups: list[dict]) -> list[dict]:
    """把过短的小节并入前一组（案例组从不被并入），使每块有足够上下文。"""
    merged: list[dict] = []
    for group in groups:
        group = {"section": group["section"], "case_no": group["case_no"],
                 "title": group["title"], "lines": list(group["lines"])}
        prev = merged[-1] if merged else None
        can_merge = (
            prev is not None
            and group["case_no"] is None            # 案例块保持独立
            and prev["case_no"] is None
            and _group_len(group) < MIN_GROUP_CHARS
            and _group_len(prev) < MAX_GROUP_CHARS
        )
        if can_merge:
            if group["title"]:
                prev["lines"].append(group["title"])
            prev["lines"].extend(group["lines"])
            if prev["section"] is None:
                prev["section"] = group["section"]
        else:
            merged.append(group)
    # 首块过短时并入后一组
    if len(merged) > 1 and _group_len(merged[0]) < MIN_GROUP_CHARS and merged[1]["case_no"] is None:
        head, second = merged[0], merged[1]
        if head["title"]:
            second["lines"].insert(0, head["title"])
        second["lines"][0:0] = head["lines"]
        merged.pop(0)
    return merged


def split_into_chunks(meta: dict, blocks: list[tuple[str, str]], chunk_size: int = 400,
                      overlap: int = 50, case_chunk_size: int = 400) -> list[Chunk]:
    """标题驱动切块：案例手册以"案例N"为界，其余以章节号为界，超长再按 chunk_size/overlap 细分。

    块长上限受 embedding 模型上下文（512 token）约束，默认 400 字；同一案例被拆开时
    locator 会带 (i/n) 序号，A4 仍可看出它们同源。"""
    groups: list[dict] = []
    current = {"section": None, "case_no": None, "title": None, "lines": []}
    for kind, text in blocks:
        if kind == "title":
            case = _RE_CASE_TITLE.match(text)
            section = _RE_SECTION_TITLE.match(text)
            is_deep = bool(re.match(r"^\d+\.\d+\.\d+", text))     # 三级及更深不作为切分点
            if case or (section and not is_deep):
                if current["lines"] or current["title"]:
                    groups.append(current)
                current = {
                    "section": (section.group(1) if section else current["section"]),
                    "case_no": (f"案例{case.group(1)}" if case else None),
                    "title": text,
                    "lines": [],
                }
            else:
                current["lines"].append(text)                          # 深层标题并入正文
            continue
        current["lines"].append(text)
    if current["lines"] or current["title"]:
        groups.append(current)

    groups = _merge_short_groups(groups)

    chunks: list[Chunk] = []
    seq = 0
    for group in groups:
        body = "\n".join(group["lines"]).strip()
        head = group["title"] or ""
        text = (head + "\n" + body).strip() if head else body
        if len(text) < 30:                      # 过滤目录/页眉等碎片
            continue
        effective = case_chunk_size if (meta["doc_type"] == "case" and group["case_no"]) else chunk_size
        parts = _split_long(text, effective, overlap)
        for idx, part in enumerate(parts):
            seq += 1
            label = group["case_no"] or group["section"] or "正文"
            locator = f"{meta['doc_short']}#{label}" + (f"({idx + 1}/{len(parts)})" if len(parts) > 1 else "")
            chunks.append(Chunk(
                chunk_id=f"{meta['doc_short']}-{seq:04d}",
                text=part,
                doc_id=meta["doc_id"],
                doc_type=meta["doc_type"],
                device_id=meta["device_id"],
                section=group["section"],
                case_no=group["case_no"],
                page=None,
                locator=locator,
                meta={"title": head, "doc_file": Path(meta["file"]).name,
                      "doc_type_cn": DOC_TYPE_CN.get(meta["doc_type"], meta["doc_type"])},
            ))
    return chunks


MAX_CHUNK_CHARS = 400      # 与 bge 上下文对齐的硬上限


def load_all_chunks(raw_dir: str | Path, chunk_size: int = 400, overlap: int = 50,
                    case_chunk_size: int = 400) -> list[Chunk]:
    chunk_size = min(chunk_size, MAX_CHUNK_CHARS)
    case_chunk_size = min(case_chunk_size, MAX_CHUNK_CHARS)
    root = Path(raw_dir)
    chunks: list[Chunk] = []
    for path in sorted(root.glob("*.docx")):
        if "传感器" in path.stem:               # 数据字段说明文档不属于知识库
            continue
        meta = meta_from_filename(path)
        blocks, _ = extract_blocks(path)
        chunks.extend(split_into_chunks(meta, blocks, chunk_size, overlap, case_chunk_size))
    return chunks
