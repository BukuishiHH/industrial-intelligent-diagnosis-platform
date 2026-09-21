# -*- coding: utf-8 -*-
"""Generate simulated sensor wide-table CSV for the IIP diagnosis platform.

Schema and thresholds follow: data/raw_docs/设备传感器数据字段与波动范围文档.docx (SENSOR-SPEC-001)
Columns: timestamp, device_id, speed, v1, v3, bearing_temp, oil_pressure, current

Scenarios (--scenario):
    normal         正常基线，全部测点落在正常区（用于"AI 不编造故障"的反向验证）
    unbalance_fj01 FJ-01 案例1：最后 24h v1 2.35->5.20 / v3 2.15->3.60，瓦温油压正常
    rub_fj01       FJ-01 案例2：最后 20min v1 2.35->8.90（10min 突变 > 2.5 mm/s，越过停机值 7.1）
    watemp_fj03    FJ-03 案例11：最后 24h 瓦温 59.5->78.0（越过二级报警 70，未到跳机 85）

Examples:
    python scripts/generate_sensor_data.py --scenario normal --start 2026-09-18T00:00:00 \
        --minutes 20 --interval 60 --seed 42 --out "data/raw_docs/设备传感器示例数据_60条.csv"
"""
import argparse
import csv
import random
from datetime import datetime, timedelta

DEVICE_PROFILES = {
    "FJ-01": {
        "speed":        {"start": 1479.0, "end": 1481.0, "noise": 0.8,  "limits": (1470.0, 1490.0), "dec": 0},
        "v1":           {"start": 2.15,   "end": 2.40,   "noise": 0.035, "limits": (1.80, 2.80),  "dec": 1},
        "v3":           {"start": 1.95,   "end": 2.20,   "noise": 0.035, "limits": (1.60, 2.80),  "dec": 1},
        "bearing_temp": {"start": 55.5,   "end": 58.0,   "noise": 0.4,   "limits": (35.0, 65.0),  "dec": 1},
        "oil_pressure": {"start": 0.240,  "end": 0.250,  "noise": 0.003, "limits": (0.15, 0.35),  "dec": 2},
        "current":      {"start": 216.0,  "end": 222.0,  "noise": 0.8,   "limits": (200.0, 228.0), "dec": 1},
    },
    "FJ-02": {
        "speed":        {"start": 979.0,  "end": 981.0,  "noise": 0.8,  "limits": (970.0, 990.0), "dec": 0},
        "v1":           {"start": 3.20,   "end": 3.40,   "noise": 0.05,  "limits": (2.50, 4.50),  "dec": 1},
        "v3":           {"start": 2.90,   "end": 3.10,   "noise": 0.05,  "limits": (2.20, 4.50),  "dec": 1},
        "bearing_temp": {"start": 62.0,   "end": 65.0,   "noise": 0.5,   "limits": (35.0, 70.0),  "dec": 1},
        "oil_pressure": {"start": 0.210,  "end": 0.220,  "noise": 0.003, "limits": (0.15, 0.25),  "dec": 2},
        "current":      {"start": 56.0,   "end": 57.5,   "noise": 0.3,   "limits": (45.0, 58.5),  "dec": 1},
    },
    "FJ-03": {
        "speed":        {"start": 989.0,  "end": 991.0,  "noise": 0.8,  "limits": (980.0, 1000.0), "dec": 0},
        "v1":           {"start": 2.05,   "end": 2.30,   "noise": 0.04,  "limits": (1.70, 2.80),   "dec": 1},
        "v3":           {"start": 1.95,   "end": 2.15,   "noise": 0.04,  "limits": (1.60, 2.80),   "dec": 1},
        "bearing_temp": {"start": 56.0,   "end": 59.5,   "noise": 0.4,   "limits": (35.0, 60.0),   "dec": 1},
        "oil_pressure": {"start": 0.240,  "end": 0.250,  "noise": 0.003, "limits": (0.15, 0.30),   "dec": 2},
        "current":      {"start": 41.0,   "end": 43.0,   "noise": 0.3,   "limits": (35.0, 45.5),   "dec": 1},
    },
}
SENSORS = ["speed", "v1", "v3", "bearing_temp", "oil_pressure", "current"]

# 故障注入场景：span 为 ("last_hours", H) / ("last_minutes", M) / ("all",)
SCENARIOS = {
    "normal": {"device": None, "title": "正常基线", "case_ref": "-", "segments": []},
    "unbalance_fj01": {
        "device": "FJ-01",
        "title": "叶轮积灰结垢导致转子不平衡",
        "case_ref": "FJ-01 故障案例手册 案例1",
        "segments": [
            {"sensor": "v1", "span": ("last_hours", 24), "start": 2.35, "end": 5.20, "noise": 0.05, "limits": (1.8, 7.1)},
            {"sensor": "v3", "span": ("last_hours", 24), "start": 2.15, "end": 3.60, "noise": 0.05, "limits": (1.6, 7.1)},
            {"sensor": "bearing_temp", "span": ("last_hours", 24), "start": 56.0, "end": 62.0, "noise": 0.4, "limits": (35.0, 74.0)},
        ],
    },
    "rub_fj01": {
        "device": "FJ-01",
        "title": "异物进入叶轮与机壳碰磨，振动突增",
        "case_ref": "FJ-01 故障案例手册 案例2",
        "segments": [
            {"sensor": "v1", "span": ("last_minutes", 20), "start": 2.35, "end": 8.90, "noise": 0.08, "limits": (1.8, 9.5)},
            {"sensor": "v3", "span": ("last_minutes", 20), "start": 2.15, "end": 5.00, "noise": 0.08, "limits": (1.6, 7.5)},
            {"sensor": "bearing_temp", "span": ("last_minutes", 20), "start": 58.0, "end": 66.0, "noise": 0.4, "limits": (35.0, 74.0)},
        ],
    },
    "watemp_fj03": {
        "device": "FJ-03",
        "title": "油冷却器水侧结垢，供油温度升高引起瓦温上升",
        "case_ref": "FJ-03 故障案例手册 案例11",
        "segments": [
            {"sensor": "bearing_temp", "span": ("last_hours", 24), "start": 59.5, "end": 78.0, "noise": 0.35, "limits": (35.0, 84.0)},
        ],
    },
}


def _span_bounds(span, count, interval_s):
    if span[0] == "all":
        return 0, count - 1
    seconds = span[1] * (3600 if span[0] == "last_hours" else 60)
    start = max(0, count - 1 - int(seconds / interval_s))
    return start, count - 1


def build_rows(device_id, start_dt, count, interval_s, rng, segments=()):
    profile = DEVICE_PROFILES[device_id]
    rows = []
    for i in range(count):
        ts = start_dt + timedelta(seconds=interval_s * i)
        ratio = i / max(1, count - 1)
        row = {"timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S+08:00"), "device_id": device_id}
        for sensor in SENSORS:
            spec = profile[sensor]
            center = spec["start"] + (spec["end"] - spec["start"]) * ratio
            value = center + rng.gauss(0.0, spec["noise"])
            lo, hi = spec["limits"]
            row[sensor] = min(max(value, lo), hi)
        rows.append(row)

    # 故障注入：窗口内线性演化，覆盖基础值
    for seg in segments:
        i0, i1 = _span_bounds(seg["span"], count, interval_s)
        dec = profile[seg["sensor"]]["dec"]
        for i in range(i0, i1 + 1):
            r = (i - i0) / max(1, i1 - i0)
            value = seg["start"] + (seg["end"] - seg["start"]) * r + rng.gauss(0.0, seg["noise"])
            lo, hi = seg["limits"]
            value = min(max(value, lo), hi)
            rows[i][seg["sensor"]] = round(value, dec) if dec else int(round(value))

    for row in rows:
        for sensor in SENSORS:
            dec = profile[sensor]["dec"]
            row[sensor] = round(row[sensor], dec) if dec else int(round(row[sensor]))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="normal", choices=sorted(SCENARIOS))
    ap.add_argument("--start", default="2026-09-15T20:00:00", help="window start, local time +08:00")
    ap.add_argument("--minutes", type=int, default=4320, help="samples per device")
    ap.add_argument("--interval", type=int, default=60, help="sampling interval in seconds")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--devices", default=",".join(DEVICE_PROFILES.keys()))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    start_dt = datetime.strptime(args.start, "%Y-%m-%dT%H:%M:%S")
    devices = [d.strip() for d in args.devices.split(",") if d.strip()]
    scenario = SCENARIOS[args.scenario]
    rng = random.Random(args.seed)

    rows = []
    for device_id in devices:
        segs = scenario["segments"] if device_id == scenario["device"] else []
        rows.extend(build_rows(device_id, start_dt, args.minutes, args.interval, rng, segs))

    with open(args.out, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["timestamp", "device_id"] + SENSORS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print("scenario=%s (%s) | rows=%d | %d devices x %d samples x %ds"
          % (args.scenario, scenario["title"], len(rows), len(devices), args.minutes, args.interval))
    print("window: %s ~ %s | seed=%d | -> %s"
          % (rows[0]["timestamp"], rows[-1]["timestamp"], args.seed, args.out))


if __name__ == "__main__":
    main()
