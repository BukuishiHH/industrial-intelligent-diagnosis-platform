# -*- coding: utf-8 -*-
"""时间窗解析（设计决策 D1）。

规则（确定性代码，不让 LLM 做时间算术）：
1. 用户明确给出起止          -> 按用户指定
2. 只给一个时间点/模糊时段    -> 以该时段中点为轴 ±36h
3. 未提及时间                -> 最近 72h（相对 data_now = 真实系统时间）

补充约束：单次窗口上限 30 天、下限 1 小时、end 不得超过 data_now；越界一律裁剪并记录说明。
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from packages.core import thresholds
from packages.schemas.diagnosis import TimeExpression

TZ = timezone(timedelta(hours=8))
CN_NUM = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
          "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}


def now_tz() -> datetime:
    return datetime.now(TZ)


def _tz(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=TZ)


def resolve_window(
    expr: TimeExpression | None,
    now: datetime | None = None,
) -> tuple[datetime, datetime, str, list[str]]:
    """返回 (start, end, note, warnings)。"""
    cfg = thresholds.defaults()
    now = _tz(now) or now_tz()
    warnings: list[str] = []
    expr = expr or TimeExpression(type="none")

    if expr.type == "range" and expr.start and expr.end:
        start, end = _tz(expr.start), _tz(expr.end)
        reason = "用户指定时间范围"
    elif expr.type == "point" and expr.center:
        center = _tz(expr.center)
        span = timedelta(hours=cfg["midpoint_span_hours"])
        start, end = center - span, center + span
        reason = f"以 {center:%Y-%m-%d %H:%M} 为中点 ±{cfg['midpoint_span_hours']}h"
    else:
        end = now
        start = now - timedelta(hours=cfg["default_window_hours"])
        reason = f"未指定时间，默认最近 {cfg['default_window_hours']} 小时"

    if start > end:
        start, end = end, start
        warnings.append("起止时间前后颠倒，已自动交换")

    if end > now:
        warnings.append(f"结束时间晚于当前时刻，已裁剪至 {now:%Y-%m-%d %H:%M}")
        end = now
    if start > end - timedelta(hours=cfg["min_window_hours"]):
        start = end - timedelta(hours=cfg["min_window_hours"])
        warnings.append(f"时间窗小于 {cfg['min_window_hours']} 小时，已按最小窗口处理")
    max_days = cfg["max_window_days"]
    if (end - start) > timedelta(days=max_days):
        start = end - timedelta(days=max_days)
        warnings.append(f"时间窗超过 {max_days} 天，已截断为最近 {max_days} 天")

    note = f"分析窗口：{start:%Y-%m-%d %H:%M} ~ {end:%Y-%m-%d %H:%M}（{reason}）"
    return start, end, note, warnings


# ---------------------------------------------------------------- 离线回退解析
_RE_LAST_N = re.compile(r"(?:最近|近|过去)\s*([0-9一二两三四五六七八九十]+)\s*(小时|钟头|天|日|周)")
_RE_DATE = re.compile(r"(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})")
_RE_MD = re.compile(r"(\d{1,2})\s*月\s*(\d{1,2})\s*[日号]")
_RE_CLOCK = re.compile(r"(\d{1,2})\s*[:点时]\s*(\d{1,2})?")


def parse_time_expression(text: str, now: datetime | None = None) -> TimeExpression:
    """规则解析（LLM 不可用时的回退）。能识别"最近N小时/天""今天/昨天/前天""X月Y日""HH:MM"。"""
    now = _tz(now) or now_tz()
    raw = text or ""

    m = _RE_LAST_N.search(raw)
    if m:
        amount = CN_NUM.get(m.group(1), None)
        if amount is None:
            amount = int(m.group(1)) if m.group(1).isdigit() else 0
        unit = m.group(2)
        hours = amount * ({"小时": 1, "钟头": 1, "天": 24, "日": 24, "周": 168}[unit])
        return TimeExpression(type="range", start=now - timedelta(hours=hours), end=now, raw_text=raw)

    day_base: datetime | None = None
    if "前天" in raw:
        day_base = (now - timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif "昨天" in raw or "昨日" in raw:
        day_base = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif "今天" in raw or "今日" in raw:
        day_base = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 先看是否为"从 X 到 Y"的显式范围
    found = [datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=TZ)
             for m in _RE_DATE.finditer(raw)]
    if not found:
        for m in _RE_MD.finditer(raw):
            try:
                found.append(datetime(now.year, int(m.group(1)), int(m.group(2)), tzinfo=TZ))
            except ValueError:
                pass
    if len(found) >= 2 and re.search(r"到|至|~|—|--", raw):
        found.sort()
        return TimeExpression(type="range", start=found[0], end=found[1], raw_text=raw)

    m = _RE_DATE.search(raw)
    if m:
        day_base = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=TZ)
    else:
        m = _RE_MD.search(raw)
        if m:
            try:
                day_base = datetime(now.year, int(m.group(1)), int(m.group(2)), tzinfo=TZ)
            except ValueError:
                day_base = None

    if day_base is not None:
        clock = _RE_CLOCK.search(raw)
        if clock:
            hour = int(clock.group(1))
            minute = int(clock.group(2)) if clock.group(2) else 0
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return TimeExpression(type="point", center=day_base.replace(hour=hour, minute=minute), raw_text=raw)
        # 整天 -> 取当天中点，由 ±36h 规则覆盖前后
        return TimeExpression(type="point", center=day_base + timedelta(hours=12), raw_text=raw)

    return TimeExpression(type="none", raw_text=raw)
