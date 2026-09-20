# 演示 SOP：设备检修诊断（BG-01）

> 版本：V1.0　　适用：MVP 端到端演示
> 关联文档：`业务场景设计_设备检修诊断.md`、`传感器数据资产说明.md`、SENSOR-SPEC-001

---

## 0. 接口速查（联调用）

| 接口 | 说明 |
| --- | --- |
| `POST /diagnosis/query` | 发起诊断，body `{query, session_id?}`；返回 `awaiting_clarification / awaiting_review / completed` |
| `POST /diagnosis/review` | 澄清回答 `{thread_id, device_id}` 或人工审核 `{thread_id, decision: confirm}` |
| `GET /diagnosis/report/{report_id}` | 取 Markdown 报告与结构化记录 |
| `GET /diagnosis/history` | 历史报告列表 |

均需 `Authorization: Bearer <token>`（任意登录用户）。

## 1. 演示目标

一条自然语言提问 → 知识（手册）+ 数据（传感器）双证据推理 → 输出**可溯源的故障原因与处置方案** → 人工确认 → 生成并持久化 Markdown 报告。

## 2. ⚠ 演示前检查清单（T-30 min 必须执行）

数据基准时间 `data_now` = **真实系统时间**，"最近 72h"永远指向"当前时刻往前 72 小时"。**若数据文件末端停留在过去，默认窗口的数据覆盖率会随时间衰减，演示会出现"该时段无数据"**。因此**每次演示前必须重跑数据生成**：

```powershell
# ① 重建本次要演示的场景数据集（示例：FJ-01 转子不平衡）
$a = (Get-Date).AddHours(-72).ToString('yyyy-MM-ddTHH:mm:ss')
python scripts\generate_sensor_data.py --scenario unbalance_fj01 --start $a --minutes 4320 ^
    --interval 60 --seed 42 --out "data\raw_docs\设备传感器仿真数据_72h_unbalance_fj01.csv"

# ② 校验：末端时间应与当前时刻相差 < 1 分钟，且关键测点达到预期值
python -c "import csv;rs=list(csv.DictReader(open('data/raw_docs/设备传感器仿真数据_72h_unbalance_fj01.csv',encoding='utf-8')));print(rs[-1]['timestamp'], rs[-1]['v1'])"
```

| # | 检查项 | 通过标准 |
| --- | --- | --- |
| 1 | 数据集已重跑 | CSV 末端时间 ≈ 当前时刻（差 < 1min） |
| 2 | 场景选择正确 | 见 §3 对照表，同一时刻只激活一个数据集 |
| 3 | 激活数据集已切换 | A3 读取的数据源指向本次要演示的 CSV |
| 4 | 知识库索引已构建 | `data/index/` 下有 `bm25.pkl` 与 `index_meta.json`；文档有变更时重跑 `scripts/build_index.py`（约 6s） |
| 4b | 数据库可用 | MySQL 可连接且已建表（`scripts/init_db.py`）；诊断记录/报告将入库 |
| 5 | **向量模型服务已启动** | WSL2 内 bge 服务在 30000 端口，`http://localhost:30000/v1/models` 可访问（**必须最先启动**，见 `环境与启动说明.md` §1） |
| 6 | 重排后端可用 | `RERANK_BACKEND=llm`（LLM 重排），或模型就绪后切 `bge` |
| 7 | 服务与页面 | API 与前端控制台可访问 |
| 8 | 大模型配额 | `deepseek-flash` 可调用、额度充足 |

## 3. 数据集 ↔ 演示脚本对照表

| # | 激活数据集 | 演示提问（user_query） | 预期诊断结论 | 预期证据 | 依据案例 |
| --- | --- | --- | --- | --- | --- |
| 1 | `设备传感器仿真数据_72h_unbalance_fj01.csv` | "FJ-01 最近振动一直往上涨，是什么原因？" | 叶轮积灰结垢导致转子不平衡 | 手册案例 1 + v1 越过报警 4.5、24h 上升 2.9 mm/s | FJ-01 案例 1 |
| 2 | `设备传感器仿真数据_72h_rub_fj01.csv` | "FJ-01 今天振动突然跳起来了，是不是出事了？" | 异物进入叶轮与机壳碰磨（紧急停机） | 手册案例 2 + v1 越过停机值 7.1、10min 突变 3.0 | FJ-01 案例 2 |
| 3 | `设备传感器仿真数据_72h_watemp_fj03.csv` | "3 号机瓦温有点高，帮我看看" | 油冷却器水侧结垢，供油温度升高引起瓦温上升 | 手册案例 11 + 瓦温越过二级报警 70 | FJ-03 案例 11 |
| 4 | `设备传感器仿真数据_72h_normal.csv` | "FJ-02 现在运行正常吗？" | **未发现明确故障征象**（置信度低） | 各测点均在正常区 | 反向用例 |

> 演示 1/2 一定不要用错数据集：unbalance 是"缓慢上升"，rub 是"突然跃升"，两者的 A4 结论和处置紧迫度（计划停机 vs 紧急停机）完全不同。

## 4. 标准演示流程（每个用例）

| 步骤 | 操作 | 讲解要点 |
| --- | --- | --- |
| 1 | 输入 user_query | 强调"用现场语言提问即可，不需要懂系统" |
| 2 | 系统澄清（如需） | 只问缺的设备/时间；演示时用**完整提问**可跳过澄清 |
| 3 | 展示检索证据 | **知识侧**：命中的手册章节与页码；**数据侧**：测点、时间窗、超限指标 |
| 4 | 展示诊断结论 | 根因 + 置信度 + **候选备选**（体现"AI 给假设"）+ 处置步骤（含安全提示） |
| 5 | 强调可溯源 | 点开任一证据可跳回手册原文 / 传感器趋势图 |
| 6 | 人工确认 | 强调 HITL：AI 结论未经确认不进入正式档案（记录确认人） |
| 7 | 生成报告 | Markdown 报告展示 + 提示已持久化，可下载 |
| 8 | 收官 | 强调"知识+数据双证据、可追溯、人机协同" |

## 5. 常见异常与处置

| 现象 | 可能原因 | 处置 |
| --- | --- | --- |
| "该时段无数据" | 数据集过期（未重跑生成脚本） | 执行 §2 的 ①，重跑并确认末端时间 |
| 诊断结论为"未发现异常" | 激活的是 normal 数据集，或窗口内数据未覆盖故障段 | 检查 §3 对照表；确认查询窗口落在最后 24h 内 |
| 只检索到别的设备的手册 | A2 设备过滤未生效 | 确认 `device_id` 槽位正确；检查 chunk 元数据是否带 `device_id` |
| 置信度异常低 | 证据不足（样本不足/检索未命中） | 查看 `data_quality.warnings` 与 `evidence_gaps`；检查索引是否就绪 |
| 重排报错/超时 | LLM 重排调用失败 | 已自动降级为 RRF 顺序（`degraded=true`），演示可继续并说明降级 |
| 澄清反复出现 | 提问未含设备位号 | 用完整提问（含 FJ-01/FJ-03）重试 |

## 6. 环境与启动（详见 `docs/环境与启动说明.md`）

顺序：**① WSL2 启动 bge 向量服务（端口 30000）→ ② 重跑传感器数据 → ③ 启动 FastAPI 服务**。

Python 解释器统一用 `D:\Anaconda\python.exe`（3.12.4）。

- [x] bge-large-zh-v1.5 经 WSL2 内 SGLang 服务提供（OpenAI 兼容，`http://localhost:30000/v1`，1024 维）
- [x] 知识库建索引：`python scripts/build_index.py`（616 块 / 约 6s，产物在 `data/index/`）
- [ ] 前端控制台地址（后端接口已就绪：`POST /diagnosis/query`、`POST /diagnosis/review`、`GET /diagnosis/report/{id}`）
- [ ] bge-reranker 下载完成后的切换步骤（`RERANK_BACKEND=bge`；当前为 LLM 重排）

## 7. 演示记录

| 日期 | 演示人 | 用例# | 数据集末端时间 | 结论是否命中预期 | 耗时 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |
