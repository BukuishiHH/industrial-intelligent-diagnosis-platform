# -*- coding: utf-8 -*-
import sys, io
from datetime import datetime
from packages.agents.a3_data import compute_digest
CASES = [
 ("FJ-01", "data/raw_docs/设备传感器仿真数据_72h_normal.csv"),
 ("FJ-01", "data/raw_docs/设备传感器仿真数据_72h_unbalance_fj01.csv"),
 ("FJ-01", "data/raw_docs/设备传感器仿真数据_72h_rub_fj01.csv"),
 ("FJ-03", "data/raw_docs/设备传感器仿真数据_72h_watemp_fj03.csv"),
]
import csv


def data_range(path, device):
    """取数据集自身的首末时间戳作为查询窗口（避免硬编码日期，数据重跑后仍可用）。"""
    with open(path, encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["device_id"] == device]
    return (datetime.fromisoformat(rows[0]["timestamp"]),
            datetime.fromisoformat(rows[-1]["timestamp"]))


for dev, path in CASES:
    start, end = data_range(path, dev)
    d = compute_digest(dev, start, end, data_path=path)
    print("=" * 100)
    print(path.split("/")[-1])
    for line in d.summary_lines:
        print("  " + line)
