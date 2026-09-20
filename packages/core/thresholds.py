# -*- coding: utf-8 -*-
"""阈值与测点配置的加载与访问。

配置来源：config/thresholds.yaml（抽取自 SENSOR-SPEC-001 表 3~6）。
设计约束：阈值一律从本模块读取，**禁止把阈值硬编码进提示词**（SENSOR-SPEC-001 §5.2）。
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml

from packages.core.config import BASE_DIR

CONFIG_PATH = BASE_DIR / "config" / "thresholds.yaml"


@lru_cache(maxsize=1)
def load_thresholds(path: str | None = None) -> dict[str, Any]:
    """加载阈值配置（带缓存）。"""
    with open(path or CONFIG_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def defaults() -> dict[str, Any]:
    return load_thresholds()["defaults"]


def device_ids() -> list[str]:
    return list(load_thresholds()["devices"].keys())


def get_device(device_id: str) -> dict[str, Any]:
    devices = load_thresholds()["devices"]
    key = (device_id or "").strip().upper()
    if key not in devices:
        raise KeyError(f"未配置的设备：{device_id}，可用：{list(devices)}")
    return devices[key]


def point_spec(device_id: str, sensor: str) -> dict[str, Any]:
    points = get_device(device_id)["points"]
    if sensor not in points:
        raise KeyError(f"{device_id} 无测点 {sensor}，可用：{list(points)}")
    return points[sensor]


def sensors_of(device_id: str) -> list[str]:
    return list(get_device(device_id)["points"].keys())


def normalize_sensor(device_id: str, name: str) -> str | None:
    """把手册/用户表述（如 VB-01X、瓦温）归一化为数据字段名（v1、bearing_temp）。"""
    if not name:
        return None
    raw = str(name).strip()
    points = get_device(device_id)["points"]
    if raw in points:
        return raw
    lowered = raw.lower()
    for sensor, spec in points.items():
        if sensor.lower() == lowered:
            return sensor
        for alias in spec.get("aliases", []):
            if str(alias).strip().lower() == lowered:
                return sensor
    return None


def normalize_sensors(device_id: str, names: list[str] | None) -> tuple[list[str], list[str]]:
    """批量归一化，返回 (识别出的字段, 未识别项)。names 为空时返回该设备全部测点。"""
    if not names:
        return sensors_of(device_id), []
    known: list[str] = []
    unknown: list[str] = []
    for name in names:
        hit = normalize_sensor(device_id, name)
        if hit and hit not in known:
            known.append(hit)
        elif not hit:
            unknown.append(str(name))
    return known, unknown


def trend_rules(device_id: str) -> list[dict[str, Any]]:
    """返回适用于该设备的趋势规则（threshold_by_device 覆盖默认阈值）。"""
    rules = []
    for rule in load_thresholds()["trend_rules"]:
        item = dict(rule)
        item["threshold"] = rule.get("threshold_by_device", {}).get(device_id, rule.get("threshold"))
        rules.append(item)
    return rules
