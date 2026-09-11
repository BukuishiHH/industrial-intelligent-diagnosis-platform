# 工业智能诊断平台（Industrial Intelligent-diagnosis Platform, IIP）项目文档集

> **文档版本**：V1.0  
> **文档状态**：设计基线稿（待评审）  
> **项目代号**：IIP  
> **文档语言**：正文中文，文件名与关键术语英文  
> **适用范围**：工业设备 AI 故障诊断平台的产品、研发、测试、交付与运维团队

> **项目状态调整说明**：由于不可抗力，项目现阶段仅能完成《工业智能诊断平台》的 **MVP（最小可行产品）**。本期交付、测试与验收以三份 MVP 设计文档（见 1.4 节）为准；原企业级文档（01-13）保留，作为后续演进与迭代基线。

---

## 1. 文档集说明

本目录面向《工业智能诊断平台》项目，提供从业务背景、需求分析、总体架构、详细设计、工程实施到测试验收的完整项目文档。文档按工业级研发流程组织，既可作为项目立项、评审、开发、测试和交付的依据，也可作为后续平台迭代的基线材料。

### 1.1 原始输入与建设目标

面向工业场景提供 AI 驱动的设备故障诊断，覆盖 **27 份工业文档（约 1109 页、5091 个向量块）**、**4 台设备 24 个传感器**，解决人工排查耗时长、经验依赖度高、知识传承困难等痛点。平台采用 **LangGraph 单图统一编排**，引入 **A2A + MCP 双协议分层架构**，将 AI 诊断推进到 **生产可用级别**。

### 1.2 文档清单

| 序号 | 文档 | 主要读者 | 说明 |
| --- | --- | --- | --- |
| 00 | [README.md](./README.md) | 全体成员 | 文档集索引、项目概览、术语与约束 |
| 01 | [01_business_background_and_pain_points.md](./docs/01_business_background_and_pain_points.md) | 业务方、产品、项目经理 | 项目痛点、业务背景、目标与价值 |
| 02 | [02_business_functions.md](./docs/02_business_functions.md) | 业务方、产品、研发 | 业务功能清单、用户角色、典型场景 |
| 03 | [03_agent_catalog_and_responsibilities.md](./docs/03_agent_catalog_and_responsibilities.md) | 架构师、算法、研发 | 智能体数量、职责、输入输出、协作关系 |
| 04 | [04_system_architecture_design.md](./docs/04_system_architecture_design.md) | 架构师、研发、运维 | 整体架构、分层设计、部署拓扑、关键技术决策 |
| 05 | [05_project_directory_structure.md](./docs/05_project_directory_structure.md) | 研发、DevOps | 工程目录、代码分层、配置与部署组织 |
| 06 | [06_development_milestone_plan.md](./docs/06_development_milestone_plan.md) | 项目经理、全体成员 | 里程碑、迭代计划、交付物与准入准出条件 |
| 07 | [07_requirements_analysis.md](./docs/07_requirements_analysis.md) | 产品、研发、测试 | 功能需求、非功能需求、数据需求、验收标准 |
| 08 | [08_technology_selection.md](./docs/08_technology_selection.md) | 架构师、研发、运维 | 技术栈、选型理由、备选方案与风险 |
| 09 | [09_dataset_and_hardware_resources.md](./docs/09_dataset_and_hardware_resources.md) | 算法、运维、采购 | 数据集、模型资源、硬件与容量规划 |
| 10 | [10_detailed_module_design.md](./docs/10_detailed_module_design.md) | 研发、测试 | 模块划分、接口、数据结构、异常处理 |
| 11 | [11_core_process_design.md](./docs/11_core_process_design.md) | 研发、算法、测试 | 诊断主流程、LangGraph 图、A2A/MCP 调用链 |
| 12 | [12_system_testing.md](./docs/12_system_testing.md) | 测试、研发、运维 | 测试策略、用例、性能、安全、验收 |
| 13 | [13_team_roles_and_responsibilities.md](./docs/13_team_roles_and_responsibilities.md) | 项目经理、全体成员 | 团队分工（占位符待填充） |

### 1.3 文档使用约定

- 文档中的量化指标若无原始输入依据，均按工业项目常见基线给出**建议值**，需在需求评审中确认。
- 标记“（假设）”的内容为合理推断，不直接作为合同或验收依据。
- 架构与接口设计采用“接口稳定、实现可替换”的原则，优先保证可测试、可观测、可回滚。
- 团队分工、人员姓名、工期日期、预算等使用占位符表示，由项目经理在项目启动会上填充。

### 1.4 MVP 阶段说明

> 原计划开发完整企业级平台，因不可抗力，现阶段仅能完成项目 **MVP**：由 2 人团队在约 8 个工作日内交付端到端可演示的 AI 故障诊断能力，砍掉分布式与重型运维组件；企业级扩展方案（A2A + MCP 分布式、K8s、完整鉴权等）作为演进参考，代码层面预留接口，可平滑升级。

**MVP 核心口径**：

- **交付形态**：单体 LangGraph 单图编排，A1 任务接收 → A2 知识检索 → A3 数据分析 → A4 故障推理 → A5 报告生成 → HITL 人工复核，全部节点与工具为进程内函数调用；
- **技术基线**：FastAPI + LangChain/LangGraph + OpenAI 兼容接口（DeepSeek）+ PostgreSQL/pgvector + ChromaDB + Redis + React 最小控制台，Docker Compose 单机部署；
- **数据规模**：27 份工业文档知识库（约 1109 页、5091 向量块）+ 4 台设备 24 路传感器（开源 + AI 仿真数据，固定随机种子可复现）；
- **关键指标**：单次诊断端到端 ≤ 60s、RAG 检索 ≤ 3s；检索命中率@5 ≥ 0.8、诊断准确率 ≥ 0.7（仿真数据）、幻觉率 ≤ 10%；
- **功能边界**：以 [MVP_01 第 2.2 节「MVP 范围 vs 企业扩展范围」](./MVP_01_项目总设计文档.md) 为准，Must 项全做，Won't 项一律不做。

**MVP 文档清单**（本期新增，与 01-13 企业级文档并存，共同构成文档集）：

| 序号 | 文档 | 主要读者 | 说明 |
| --- | --- | --- | --- |
| MVP-01 | [MVP_01_项目总设计文档.md](./MVP_01_项目总设计文档.md) | 全体成员 | 业务背景与痛点、目标与范围（MVP/企业双档）、用户角色与场景、需求（FR/NFR）、智能体职责（A1-A5）、技术选型、系统架构、LangGraph 编排、工具与存储设计、风险清单 |
| MVP-02 | [MVP_02_模块与核心流程设计.md](./MVP_02_模块与核心流程设计.md) | 研发、算法、测试 | 数据集与硬件资源、七大模块（M01-M07）详细设计、核心业务流程图、工程目录结构、数据模型 DDL、错误码规范 |
| MVP-03 | [MVP_03_开发计划、测试与交付.md](./MVP_03_开发计划、测试与交付.md) | 项目经理、全体成员 | 开发里程碑（M0-M7）与 Sprint/WBS、测试方案与 AI 评测指标、交付验收标准（AC-01~AC-09）、团队分工、Git/CI 规范、待确认事项 |

---

## 2. 项目概览

### 2.1 一句话定位

以工业文档知识为“应然依据”、以设备传感器数据为“实然证据”，通过 **LangGraph 单图统一编排** 与 **A2A + MCP 双协议分层架构**，构建可解释、可追溯、可扩展、可持续学习的工业设备智能诊断平台。

### 2.2 核心能力

1. **工业文档知识库**：27 份工业文档解析、OCR、结构化切块、向量化、混合检索与原文溯源。
2. **传感器数据接入与分析**：4 台设备、24 个传感器的实时/历史数据接入、清洗、特征提取与异常检测。
3. **AI 故障诊断**：基于“假设—验证”的多步诊断推理，输出候选故障、根因、置信度、证据链和处置建议。
4. **统一编排与协议分层**：LangGraph 负责流程与状态；MCP 标准化封装工具/数据；A2A 负责 Agent 协作。
5. **生产级支撑**：权限、审计、可观测、降级、重试、限流、成本控制与人工复核。
6. **知识回流**：诊断案例、专家反馈和工单结果沉淀为组织知识资产。

### 2.3 建议技术基线

| 领域 | 建议基线 | 备注 |
| --- | --- | --- |
| 编排框架 | LangGraph | 单图统一编排、Checkpoint、Human-in-the-loop |
| 协作协议 | A2A | Agent 注册、发现、任务下发与结果回传 |
| 工具协议 | MCP | 工具/数据源 Server/Client 标准化接入 |
| 大语言模型 | 支持私有化部署的工业/通用 LLM | 具体型号由选型评审确定 |
| 向量检索 | 向量库 + 关键词 + Rerank | 混合检索，结果可溯源 |
| 时序存储 | 工业时序数据库 | 支持高频写入与窗口查询 |
| 服务框架 | Python/FastAPI 为主，Java/Go 按需 | 与 AI 生态兼容 |
| 部署方式 | Kubernetes / Docker Compose | 支持私有化、网络隔离与水平扩展 |
| 可观测 | OpenTelemetry + Prometheus + Grafana + Loki | 全链路 Trace/Metric/Log |

---

## 3. 术语表

| 术语 | 英文/缩写 | 说明 |
| --- | --- | --- |
| IIP | Industrial Intelligent-diagnosis Platform | 工业智能诊断平台 |
| Agent | Agent | 具备自主规划、工具调用和结果生成能力的智能体 |
| LangGraph | LangGraph | 用于构建有状态多步骤 Agent 流程的图编排框架 |
| MCP | Model Context Protocol | 模型上下文协议，标准化接入工具与数据源 |
| A2A | Agent-to-Agent | 智能体之间协作、发现与任务通信的协议层 |
| RAG | Retrieval-Augmented Generation | 检索增强生成 |
| Rerank | Rerank | 对初步召回结果进行精排 |
| Chunk | Chunk | 文档切分后的向量化文本块 |
| HITL | Human-in-the-loop | 关键环节人工确认与介入 |
| MTTR | Mean Time To Repair | 平均修复时间 |
| RTO/RPO | Recovery Time/Point Objective | 恢复时间目标/恢复点目标 |
| SOP | Standard Operating Procedure | 标准作业程序 |

---

## 4. 文档维护与变更

| 变更类型 | 触发条件 | 责任角色 | 输出 |
| --- | --- | --- | --- |
| 基线冻结 | 需求评审通过 | 项目经理/产品负责人 | 冻结版本、变更记录 |
| 设计变更 | 架构评审或关键技术验证后 | 架构师 | 架构决策记录、设计更新 |
| 接口变更 | 模块联调前 | 模块负责人 | 接口文档、兼容性说明 |
| 测试策略变更 | 需求或架构变化 | 测试负责人 | 测试计划与用例更新 |
| 发布变更 | 上线前 | 发布经理 | 发布说明、回滚方案 |

## 5. 项目详细文档
- [需求规格说明书 SRS](./docs/IIP-SRS.md)
- [开发协作规范](./docs/contributing.md)
- [MVP 项目总设计文档](./MVP_01_项目总设计文档.md)
- [MVP 模块与核心流程设计](./MVP_02_模块与核心流程设计.md)
- [MVP 开发计划、测试与交付](./MVP_03_开发计划、测试与交付.md)