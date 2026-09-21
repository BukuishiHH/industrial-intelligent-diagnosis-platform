# -*- coding: utf-8 -*-
"""A3 数据检索节点。

职责（设计文档 §5）：把 A1 给出的结构化槽位（device_id + 时间窗 + 测点）变成
「统计特征 + 阈值/趋势判定 + 数据可用性」的 SensorDigest。

设计约束：
- **原始时序绝不进 prompt**：只输出特征摘要与降采样序列（降采样序列仅供前端画图）。
- 阈值/趋势限值一律读 config/thresholds.yaml，禁止硬编码。
- 样本不足时对应趋势规则**不判定**并写入 warnings（例如窗口只有 20min 却要判"24h 上升"）。
- 缺失率 > 10% 必须写入 warnings。
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd

from packages.core import thresholds
from packages.core.config import BASE_DIR
from packages.schemas.diagnosis import (
    DataQuality,
    SensorDigest,
    SensorStats,
    ThresholdHit,
    TrendHit,
)

TZ = timezone(timedelta(hours=8))
DEFAULT_DATA_FILE = "设备传感器仿真数据_72h_normal.csv"
LEVELS = ["normal", "warning", "alarm", "trip"]


# ---------------------------------------------------------------- 数据加载
def resolve_data_path(path: str | None = None) -> Path:
    """数据源：显式参数 > 环境变量 SENSOR_DATA_PATH > 默认数据集。"""
    raw = path or os.getenv("SENSOR_DATA_PATH") or str(BASE_DIR / "data" / "raw_docs" / DEFAULT_DATA_FILE)
    p = Path(raw)
    return p if p.is_absolute() else (BASE_DIR / p)


@lru_cache(maxsize=4)
def _load_frame(path_str: str) -> pd.DataFrame:
    df = pd.read_csv(path_str, encoding="utf-8")
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601")
    return df.sort_values("timestamp").reset_index(drop=True)


def load_sensor_frame(path: str | None = None) -> pd.DataFrame:
    return _load_frame(str(resolve_data_path(path)))


def _as_tz(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=TZ)


# ---------------------------------------------------------------- 阈值判定
def classify_value(value: float, spec: dict[str, Any]) -> int:
    """单点级别：0 正常 / 1 预警（超正常区未达报警）/ 2 报警 / 3 停机。"""
    trip, alarm, normal = spec.get("trip", {}), spec.get("alarm", {}), spec.get("normal", {})
    if "high" in trip and value > trip["high"]:
        return 3
    if "low" in trip and value < trip["low"]:
        return 3
    if "high" in alarm and value >= alarm["high"]:
        return 2
    if "low" in alarm and value <= alarm["low"]:
        return 2
    if "max" in normal and value > normal["max"]:
        return 1
    if "min" in normal and value < normal["min"]:
        return 1
    return 0


def _first_limit(spec: dict[str, Any], level: str) -> float | None:
    limits = spec.get(level, {})
    return limits.get("high") if "high" in limits else limits.get("low")


# ---------------------------------------------------------------- 统计特征
def _stats_for(y: pd.Series, ts: pd.Series, sensor: str, spec: dict[str, Any]) -> SensorStats:
    arr = y.to_numpy(dtype=float)
    levels = np.array([classify_value(v, spec) for v in arr], dtype=int)
    status_idx = int(levels.max()) if len(levels) else 0
    alarm_mask = levels >= 2
    trip_mask = levels >= 3

    hours = (ts.iloc[-1] - ts.iloc[0]).total_seconds() / 3600 if len(ts) > 1 else 0.0
    slope = float(np.polyfit(np.linspace(0, hours, len(arr)), arr, 1)[0]) if len(arr) > 2 and hours > 0 else None
    offset = 10  # 10 分钟（按 1min 采样）

    return SensorStats(
        sensor=sensor,
        unit=spec.get("unit", ""),
        count=len(arr),
        first=round(float(arr[0]), 4),
        last=round(float(arr[-1]), 4),
        mean=round(float(arr.mean()), 4),
        max=round(float(arr.max()), 4),
        min=round(float(arr.min()), 4),
        rms=round(float(np.sqrt(np.mean(arr ** 2))), 4),
        std=round(float(arr.std(ddof=0)), 4),
        peak_to_peak=round(float(arr.max() - arr.min()), 4),
        trend_slope_per_hour=round(slope, 4) if slope is not None else None,
        change_over_window=round(float(arr[-1] - arr[0]), 4),
        max_delta_10min=round(float(np.abs(arr[offset:] - arr[:-offset]).max()), 4) if len(arr) > offset else None,
        status=LEVELS[status_idx],
        over_alarm_count=int(alarm_mask.sum()),
        first_over_alarm_time=ts.iloc[int(np.argmax(alarm_mask))].to_pydatetime() if alarm_mask.any() else None,
        over_trip_count=int(trip_mask.sum()),
    )


# ---------------------------------------------------------------- 趋势规则
def _eval_rule(rule: dict[str, Any], y: pd.Series, ts: pd.Series, interval_s: int,
               covered_hours: float) -> tuple[TrendHit | None, str | None]:
    """返回 (命中, 跳过原因)。"""
    rtype = rule["type"]
    sensor = rule["sensors"][0]
    if rtype == "unsupported":
        return None, f"规则 {rule['id']} 无法判定：{rule.get('conclusion', '')}"

    arr = y.to_numpy(dtype=float)
    if rtype == "rise_over_window":
        need = rule["window_hours"]
        if covered_hours < need * 0.95:
            return None, f"规则 {rule['id']} 未判定：窗口覆盖 {covered_hours:.1f}h < 需要 {need}h（样本不足）"
        n = int(need * 3600 / interval_s) + 1
        seg = arr[-n:] if len(arr) >= n else arr
        value = float(seg.max() - seg[0])
        unit = rule.get("unit", "")
        # 区分渐变型与突变型上升，供 A4 选择根因（积灰结垢 vs 碰磨/损伤）
        # 判据：最后 1 小时的上升量占总上升量的比例
        m1h = min(len(seg), max(1, int(3600 / interval_s)))
        jump = float(seg[-1] - seg[-m1h]) if len(seg) > 1 else 0.0
        detail = f"{sensor} 窗口内由 {seg[0]:.1f} 升至 {seg.max():.1f} {unit}（+{value:.1f}）"
        if value > 0 and jump / value > 0.5:
            detail += "；上升集中在最后 1h 内，属突变型，优先考虑碰磨、轴承损伤、对中破坏"
        else:
            detail += "；上升历时较长，属渐变型，优先考虑积灰结垢等渐进性因素"
    elif rtype == "jump_in_window":
        need_min = rule["window_minutes"]
        if covered_hours * 60 < need_min:
            return None, f"规则 {rule['id']} 未判定：窗口覆盖 {covered_hours * 60:.0f}min < 需要 {need_min}min（样本不足）"
        m = max(1, int(need_min * 60 / interval_s))
        if len(arr) <= m:
            return None, f"规则 {rule['id']} 未判定：有效点数不足"
        diff = np.abs(arr[m:] - arr[:-m])
        idx = int(np.argmax(diff))
        value = float(diff[idx])
        unit = rule.get("unit", "")
        detail = (f"{sensor} 在 {need_min}min 内由 {arr[idx]:.1f} 突变为 {arr[idx + m]:.1f} {unit}"
                  f"（Δ{value:.1f}）")
    elif rtype == "rise_rate":
        need_min = rule["window_minutes"]
        if covered_hours * 60 < need_min:
            return None, f"规则 {rule['id']} 未判定：窗口覆盖 {covered_hours * 60:.0f}min < 需要 {need_min}min（样本不足）"
        m = max(1, int(need_min * 60 / interval_s))
        if len(arr) <= m:
            return None, f"规则 {rule['id']} 未判定：有效点数不足"
        delta = arr[m:] - arr[:-m]
        idx = int(np.argmax(delta))
        value = float(delta[idx]) / (need_min / 60)
        unit = rule.get("unit", "")
        detail = f"{sensor} 在 {need_min}min 内上升 {delta[idx]:.1f}，折合 {value:.1f} {unit}"
    elif rtype == "fluctuation_per_minute":
        if len(arr) < 2:
            return None, f"规则 {rule['id']} 未判定：有效点数不足"
        diffs = np.abs(np.diff(arr))
        over = diffs > rule["threshold"]
        # 持续性要求：孤立尖峰（常见于测量量化噪声）不算异常波动
        if int(over.sum()) < 2:
            return None, None
        value = float(diffs.max())
        unit = rule.get("unit", "")
        detail = f"{sensor} 相邻采样最大波动 {value:.3f} {unit}（越限 {int(over.sum())} 次）"
    elif rtype == "steady_fluctuation":
        if len(arr) < 3:
            return None, f"规则 {rule['id']} 未判定：有效点数不足"
        value = float((arr.max() - arr.min()) / 2)
        unit = rule.get("unit", "")
        detail = f"{sensor} 稳态波动 ±{value:.0f} {unit}（范围 {arr.min():.0f}~{arr.max():.0f}）"
    else:
        return None, f"规则 {rule['id']} 类型 {rtype} 未实现"

    if value > rule["threshold"]:
        return TrendHit(
            rule_id=rule["id"], sensor=sensor, value=round(value, 3),
            threshold=rule["threshold"], unit=rule.get("unit", ""),
            conclusion=rule.get("conclusion", ""), case_hint=rule.get("case_hint"), detail=detail,
        ), None
    return None, None


# ---------------------------------------------------------------- 主入口
def compute_digest(
    device_id: str,
    start: datetime | None,
    end: datetime | None,
    sensors: Sequence[str] | None = None,
    data_path: str | None = None,
    include_series: bool = True,
    series_points: int = 40,
) -> SensorDigest:
    """查询指定设备在 [start, end] 的传感器数据并生成特征摘要。"""
    device_id = (device_id or "").strip().upper()
    device = thresholds.get_device(device_id)
    start, end = _as_tz(start), _as_tz(end)

    df = load_sensor_frame(data_path)
    df = df[df["device_id"] == device_id]
    if start is not None:
        df = df[df["timestamp"] >= start]
    if end is not None:
        df = df[df["timestamp"] <= end]
    df = df.sort_values("timestamp").reset_index(drop=True)

    wanted, unknown = thresholds.normalize_sensors(device_id, list(sensors) if sensors else None)
    warnings: list[str] = []
    if unknown:
        warnings.append(f"未识别的测点：{', '.join(unknown)}（已忽略）")

    if df.empty:
        return SensorDigest(
            digest_id=f"sd_{device_id}_{(end or datetime.now(TZ)).strftime('%Y%m%d%H%M')}",
            device_id=device_id, device_model=device.get("model"), start=start, end=end,
            data_quality=DataQuality(warnings=warnings + ["该时间窗内无任何数据"]),
            empty=True, summary_lines=[f"{device_id} 在指定时间窗内无数据"], sensors=[],
        )

    counts = df["timestamp"].diff().dt.total_seconds().dropna()
    interval_s = int(counts.median()) if len(counts) else 60
    covered_hours = (df["timestamp"].iloc[-1] - df["timestamp"].iloc[0]).total_seconds() / 3600
    requested_hours = None
    if start is not None and end is not None:
        requested_hours = (end - start).total_seconds() / 3600
    expected = int(round((requested_hours or covered_hours) * 3600 / interval_s)) + 1 if interval_s else None
    coverage = (covered_hours / requested_hours) if requested_hours else None
    missing_rate = max(0.0, 1 - len(df) / expected) if expected else None

    stats: list[SensorStats] = []
    hits: list[ThresholdHit] = []
    for sensor in wanted:
        spec = device["points"][sensor]
        y, ts = df[sensor].astype(float), df["timestamp"]
        st = _stats_for(y, ts, sensor, spec)
        stats.append(st)
        if st.status in ("alarm", "trip"):
            limit = _first_limit(spec, "trip" if st.status == "trip" else "alarm")
            extreme = st.max if (spec.get("alarm", {}).get("high") is not None) else st.min
            hits.append(ThresholdHit(
                sensor=sensor, level=st.status, value=extreme or 0.0, limit=limit or 0.0,
                at=st.first_over_alarm_time,
                description=(f"{sensor} 达到{('停机' if st.status == 'trip' else '报警')}值 "
                             f"{limit}{spec.get('unit', '')}，实测极值 {extreme}{spec.get('unit', '')}"
                             f"，累计 {st.over_alarm_count} 点越限"),
            ))

    trend_hits: list[TrendHit] = []
    for rule in thresholds.trend_rules(device_id):
        rule_sensors = [s for s in rule["sensors"] if s in wanted]
        if not rule_sensors:
            continue
        hit, skip = _eval_rule(rule, df[rule_sensors[0]].astype(float), df["timestamp"], interval_s, covered_hours)
        if hit:
            trend_hits.append(hit)
        elif skip:
            warnings.append(skip)

    if missing_rate is not None and missing_rate > thresholds.defaults()["missing_rate_warn"]:
        warnings.append(f"数据缺失率 {missing_rate:.1%} 超过 10%，结论可靠性下降")
    if coverage is not None and coverage < 0.99:
        warnings.append(f"时间窗覆盖率 {coverage:.1%}（{covered_hours:.1f}h / {requested_hours:.1f}h）")

    quality = DataQuality(
        points=len(df), expected_points=expected, interval_seconds=interval_s,
        requested_hours=round(requested_hours, 2) if requested_hours else None,
        covered_hours=round(covered_hours, 2), coverage=round(coverage, 3) if coverage else None,
        missing_rate=round(missing_rate, 4) if missing_rate is not None else None,
        warnings=warnings,
    )

    series: dict[str, list[float]] = {}
    series_ts: list[str] = []
    if include_series:
        idx = (np.linspace(0, len(df) - 1, series_points).astype(int)
               if len(df) > series_points else np.arange(len(df)))
        series_ts = [df["timestamp"].iloc[i].isoformat() for i in idx]
        for st in stats:
            series[st.sensor] = [round(float(df[st.sensor].iloc[i]), 3) for i in idx]

    digest = SensorDigest(
        digest_id=f"sd_{device_id}_{df['timestamp'].iloc[-1].strftime('%Y%m%d%H%M')}",
        device_id=device_id, device_model=device.get("model"),
        start=df["timestamp"].iloc[0].to_pydatetime(), end=df["timestamp"].iloc[-1].to_pydatetime(),
        sensors=stats, threshold_hits=hits, trend_hits=trend_hits, data_quality=quality,
        series=series, series_timestamps=series_ts,
    )
    digest.summary_lines = summarize(digest)
    return digest


def summarize(digest: SensorDigest) -> list[str]:
    """生成给 A4 prompt 用的紧凑文本（原始时序不进 prompt）。"""
    q = digest.data_quality
    lines = [
        f"设备 {digest.device_id}（{digest.device_model or '型号未知'}）"
        f"，窗口 {digest.start:%Y-%m-%d %H:%M} ~ {digest.end:%Y-%m-%d %H:%M}"
        f"，{q.points} 点 / 间隔 {q.interval_seconds}s / 覆盖 {q.covered_hours}h"
        + (f" / 缺失率 {q.missing_rate:.1%}" if q.missing_rate is not None else "")
    ]
    for st in digest.sensors:
        seg = (f"{st.sensor}({st.unit})：均值 {st.mean}，最大 {st.max}，最小 {st.min}，"
               f"末值 {st.last}，趋势 {st.trend_slope_per_hour}/h，状态 {st.status}")
        if st.max_delta_10min is not None:
            seg += f"，10min 最大突变 {st.max_delta_10min}"
        if st.over_alarm_count:
            seg += f"，越限 {st.over_alarm_count} 点，首超 {st.first_over_alarm_time:%Y-%m-%d %H:%M}"
        lines.append(seg)
    for hit in digest.threshold_hits:
        lines.append(f"[阈值命中] {hit.description}")
    for hit in digest.trend_hits:
        lines.append(f"[趋势命中] {hit.detail} → {hit.conclusion}（依据：{hit.case_hint}）")
    for w in digest.data_quality.warnings:
        lines.append(f"[数据提示] {w}")
    return lines
