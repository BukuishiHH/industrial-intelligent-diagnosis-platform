# -*- coding: utf-8 -*-
"""统一回归测试入口。

用法：
    python scripts/run_all_checks.py            # 全量（含调用大模型的端到端用例，约 2~3 分钟）
    python scripts/run_all_checks.py --fast     # 只跑不依赖大模型的用例（约 20 秒）

各用例以独立脚本形式存在，也可单独执行。
"""
from __future__ import annotations

import runpy
import sys
import time
import traceback

# (用例名, [[脚本, 可选argv...], ...], 是否依赖大模型)
# 多段用例用于"跨进程"场景（checkpoint 持久化必须换进程才能证明真的落盘）
CHECKS: list[tuple[str, list[list[str]], bool]] = [
    ("环境/依赖/向量服务/数据库", [["scripts/check_env.py"]], False),
    ("时间窗解析 + A1 规则回退", [["scripts/check_a1_timewindow.py"]], False),
    ("A3 特征与阈值判定（4 个数据集）", [["scripts/check_a3_digest.py"]], False),
    ("文档切块 + BM25", [["scripts/check_chunking.py"]], False),
    ("用户隔离（历史/报告/会话越权）", [["scripts/check_user_isolation.py"]], False),
    ("MySQL 落库 + checkpoint 跨进程恢复", [["scripts/check_persistence.py", "1"],
                                            ["scripts/check_persistence.py", "2"]], True),
    ("A2 混合检索 + 重排", [["scripts/check_retrieval.py"]], True),
    ("端到端 A1→A3→A2→A4→A5", [["scripts/check_a5_report.py"]], True),
    ("LangGraph 图（澄清/审核中断）", [["scripts/check_graph_e2e.py"]], True),
    ("FastAPI 接口（含 401）", [["scripts/check_api.py"]], True),
]


def main() -> int:
    fast = "--fast" in sys.argv
    results: list[tuple[str, str, float]] = []
    print("=" * 78)
    print("IIP 设备检修诊断 — 回归测试" + ("（快速模式：跳过大模型用例）" if fast else "（全量）"))
    print("=" * 78)
    for name, commands, needs_llm in CHECKS:
        if fast and needs_llm:
            results.append((name, "跳过", 0.0))
            print("\n---- [跳过] " + name + "（需要大模型）")
            continue
        print("\n---- [执行] " + name + "  (" + " ; ".join(" ".join(c) for c in commands) + ")")
        started = time.time()
        status = "通过"
        for command in commands:
            script, *argv = command
            saved_stdout = sys.stdout
            saved_argv = sys.argv
            try:
                sys.argv = [script] + argv
                runpy.run_path(script, run_name="__main__")
            except SystemExit as exc:
                if exc.code not in (0, None):
                    status = "失败(exit=%s)" % exc.code
                    break
            except Exception as exc:                  # noqa: BLE001
                status = "失败: " + type(exc).__name__
                traceback.print_exc()
                break
            finally:
                sys.stdout = saved_stdout              # 用例可能替换过 stdout，逐一还原
                sys.argv = saved_argv
        elapsed = time.time() - started
        results.append((name, status, elapsed))
        print("---- [%s] %s（%.1fs）" % (status, name, elapsed))

    print("\n" + "=" * 78)
    print("汇总")
    print("=" * 78)
    failed = 0
    for name, status, elapsed in results:
        print("  %-36s %-16s %6.1fs" % (name, status, elapsed))
        if status.startswith("失败"):
            failed += 1
    print("\n结果：%d 项通过 / %d 项失败 / %d 项跳过"
          % (sum(1 for _, s, _ in results if s == "通过"), failed,
             sum(1 for _, s, _ in results if s == "跳过")))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
