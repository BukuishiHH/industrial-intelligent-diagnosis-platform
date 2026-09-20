# -*- coding: utf-8 -*-
import sys, io
from datetime import datetime
from packages.core.timewindow import resolve_window, parse_time_expression, TZ
from packages.agents.a1_intent import recognize_by_rules, build_clarification_card
from packages.schemas.diagnosis import TimeExpression

NOW = datetime(2026, 9, 18, 19, 55, tzinfo=TZ)
print("== 时间窗规则 ==")
cases = [
    ("明确起止", TimeExpression(type="range", start=datetime(2026,9,14,0,0), end=datetime(2026,9,14,9,0))),
    ("单点 9/17 08:00", TimeExpression(type="point", center=datetime(2026,9,17,8,0))),
    ("未指定", TimeExpression(type="none")),
    ("未来时间", TimeExpression(type="range", start=datetime(2026,9,18,0,0), end=datetime(2026,9,25,0,0))),
    ("超长窗口", TimeExpression(type="range", start=datetime(2026,1,1), end=datetime(2026,9,18))),
]
for name, expr in cases:
    s, e, note, warns = resolve_window(expr, now=NOW)
    print(f"  [{name}] {s:%m-%d %H:%M} ~ {e:%m-%d %H:%M} | {note} | warns={warns}")

print("\n== 自然语言时间回退解析 ==")
for q in ["最近3天振动大", "昨天上午的振动", "9月17日8点的数据", "2026-09-16 到 2026-09-17", "帮我看看"]:
    e = parse_time_expression(q, now=NOW)
    print(f"  {q!r} -> type={e.type} start={e.start} center={e.center} end={e.end}")

print("\n== A1 规则回退（无 LLM）==")
for q in ["FJ-01 最近振动一直往上涨是什么原因", "3号机瓦温有点高帮我看看", "1号机昨天上午振动突然跳起来了",
          "FJ-02 现在运行正常吗", "今天天气怎么样", "设备有异响，油压也掉了"]:
    r = recognize_by_rules(q, now=NOW)
    print(f"  {q!r}\n     intent={r.intent} device={r.device_id} sensors={r.sensor_hint} "
          f"time={r.time_expression.type} missing={r.missing_slots}")

card = build_clarification_card(recognize_by_rules("振动有点大", now=NOW))
print("\n== 澄清卡片 ==")
print("  summary:", card.summary)
for o in card.options:
    print("   -", o["label"])
