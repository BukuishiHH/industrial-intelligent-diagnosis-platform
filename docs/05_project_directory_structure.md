# 05 工程目录结构（Project Directory Structure）

> 文档编号：IIP-ENG-001  
> 版本：V1.0  
> 状态：评审稿  
> 读者：后端/算法/前端/测试/DevOps 工程师

---

## 1. 工程组织原则

1. **单仓库（Monorepo）为主**：应用、服务、算法、前端、部署、文档统一仓库，便于跨模块变更和版本对齐。
2. **按领域分层**：目录体现“接入—编排—协议—能力—数据—基础设施”的架构分层。
3. **契约先行**：接口 Schema、数据模型、A2A/MCP 能力描述先于实现提交评审。
4. **可独立部署**：每个 Agent/服务有独立入口、配置、测试和 Dockerfile。
5. **测试与代码同目录**：单元测试、集成测试、契约测试、端到端测试按层放置。
6. **配置外置**：环境相关配置通过环境变量/配置中心注入，代码中不硬编码密钥。
7. **文档即代码**：架构、接口、运维文档与代码同仓库维护。

---

## 2. 推荐目录结构

```text
industrial-ai-diagnosis-platform/
├── README.md
├── LICENSE
├── Makefile
├── pyproject.toml
├── package.json
├── pnpm-workspace.yaml
├── .editorconfig
├── .gitignore
├── .pre-commit-config.yaml
├── .env.example
├── docker-compose.yml
├── docker-compose.observability.yml
│
├── docs/                                  # 项目文档（本目录）
│   ├── README.md
│   ├── 01_business_background_and_pain_points.md
│   ├── 02_business_functions.md
│   ├── 03_agent_catalog_and_responsibilities.md
│   ├── 04_system_architecture_design.md
│   ├── 05_project_directory_structure.md
│   ├── 06_development_milestone_plan.md
│   ├── 07_requirements_analysis.md
│   ├── 08_technology_selection.md
│   ├── 09_dataset_and_hardware_resources.md
│   ├── 10_detailed_module_design.md
│   ├── 11_core_process_design.md
│   ├── 12_system_testing.md
│   ├── 13_team_roles_and_responsibilities.md
│   └── assets/
│       ├── images/
│       └── diagrams/
│
├── contracts/                             # 接口契约与 Schema
│   ├── a2a/
│   │   ├── agent-card.schema.json
│   │   ├── task-request.schema.json
│   │   ├── task-response.schema.json
│   │   └── capabilities.yaml
│   ├── mcp/
│   │   ├── tool-registry.yaml
│   │   ├── document.search.schema.json
│   │   ├── tsdb.query.schema.json
│   │   ├── tsdb.features.schema.json
│   │   ├── report.render.schema.json
│   │   └── notify.send.schema.json
│   ├── api/
│   │   ├── openapi.yaml
│   │   └── asyncapi.yaml
│   └── data/
│       ├── diagnosis-state.schema.json
│       ├── evidence.schema.json
│       ├── diagnosis-result.schema.json
│       └── device-metadata.schema.json
│
├── apps/                                  # 可独立运行的应用/服务
│   ├── api-gateway/                       # API 网关/BFF
│   │   ├── src/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── README.md
│   ├── web-console/                       # Web 控制台
│   │   ├── src/
│   │   ├── public/
│   │   ├── tests/
│   │   └── Dockerfile
│   ├── orchestrator/                      # LangGraph 单图编排服务
│   │   ├── src/
│   │   │   ├── graph/
│   │   │   │   ├── builder.py
│   │   │   │   ├── state.py
│   │   │   │   ├── nodes/
│   │   │   │   └── edges/
│   │   │   ├── checkpointer/
│   │   │   ├── policies/
│   │   │   └── main.py
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── README.md
│   ├── agent-runtime/                     # 通用 Agent 运行时/SDK
│   │   ├── src/
│   │   └── tests/
│   ├── agents/                            # 10 个核心 Agent
│   │   ├── a01_orchestrator/
│   │   ├── a02_intake_triage/
│   │   ├── a03_knowledge_retrieval/
│   │   ├── a04_sensor_data/
│   │   ├── a05_anomaly_detection/
│   │   ├── a06_fault_diagnosis/
│   │   ├── a07_evidence_verification/
│   │   ├── a08_maintenance_decision/
│   │   ├── a09_report_communication/
│   │   └── a10_knowledge_feedback/
│   ├── mcp-servers/                       # MCP 工具服务
│   │   ├── document_search_server/
│   │   ├── tsdb_server/
│   │   ├── feature_server/
│   │   ├── device_registry_server/
│   │   ├── case_server/
│   │   ├── report_server/
│   │   ├── notification_server/
│   │   └── model_gateway_server/
│   ├── a2a-registry/                      # A2A 注册与发现服务
│   └── a2a-gateway/                       # A2A 任务网关
│
├── services/                              # 领域服务/后端能力
│   ├── document-ingestion/                # 文档解析、OCR、切块、向量化
│   ├── retrieval-service/                 # 混合检索与 Rerank
│   ├── sensor-ingestion/                  # 传感器数据采集与协议适配
│   ├── time-series-service/               # 时序查询与特征计算
│   ├── anomaly-service/                   # 异常检测算法服务
│   ├── diagnosis-service/                 # 诊断领域服务（规则、故障库）
│   ├── report-service/                    # 报告生成与导出
│   ├── notification-service/              # 通知与推送
│   ├── feedback-service/                  # 案例与反馈管理
│   ├── iam-service/                       # 认证授权
│   ├── audit-service/                     # 审计日志
│   ├── config-service/                    # 配置管理
│   └── observability-service/             # 指标、Trace、成本
│
├── packages/                              # 可复用 Python/TS 包
│   ├── iip-common/                        # 通用工具、异常、日志、时间
│   ├── iip-contracts/                     # Schema 生成与校验
│   ├── iip-a2a-sdk/                       # A2A 客户端/服务端 SDK
│   ├── iip-mcp-sdk/                       # MCP 客户端/服务端 SDK
│   ├── iip-evidence/                      # 证据数据结构与校验
│   ├── iip-security/                      # 鉴权、脱敏、提示注入防护
│   ├── iip-observability/                 # Trace/Metric 埋点
│   └── iip-testkit/                       # 测试夹具与 Mock
│
├── ml/                                    # 算法与模型工程
│   ├── datasets/
│   │   ├── raw/
│   │   ├── interim/
│   │   ├── processed/
│   │   └── evaluation/
│   ├── notebooks/
│   ├── training/
│   │   ├── anomaly_detection/
│   │   ├── embedding_finetune/
│   │   └── rerank_finetune/
│   ├── evaluation/
│   │   ├── retrieval/
│   │   ├── diagnosis/
│   │   └── safety/
│   ├── prompts/
│   │   ├── a02_intake/
│   │   ├── a03_retrieval/
│   │   ├── a06_diagnosis/
│   │   └── a07_verification/
│   └── model-cards/
│
├── data/                                  # 数据样例与初始化数据（不含敏感数据）
│   ├── samples/
│   ├── seed/
│   │   ├── devices.json
│   │   ├── sensors.json
│   │   ├── fault-library.json
│   │   └── diagnosis-sops.json
│   └── README.md
│
├── infra/                                 # 基础设施与部署
│   ├── docker/
│   │   ├── Dockerfile.base
│   │   └── entrypoint.sh
│   ├── kubernetes/
│   │   ├── base/
│   │   ├── overlays/
│   │   │   ├── dev/
│   │   │   ├── staging/
│   │   │   └── production/
│   │   ├── secrets.example.yaml
│   │   └── network-policies/
│   ├── terraform/
│   ├── helm/
│   ├── monitoring/
│   │   ├── prometheus/
│   │   ├── grafana/
│   │   ├── loki/
│   │   └── otel/
│   └── scripts/
│       ├── bootstrap.sh
│       ├── db-migrate.sh
│       ├── index-rebuild.sh
│       └── backup-restore.sh
│
├── tests/                                 # 跨服务测试
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── e2e/
│   ├── performance/
│   ├── security/
│   └── fixtures/
│
├── tools/                                 # 开发与运维工具
│   ├── cli/
│   ├── schema-validator/
│   ├── mock-mcp-server/
│   └── mock-a2a-agent/
│
├── scripts/                               # 仓库级脚本
│   ├── lint.sh
│   ├── test.sh
│   ├── build.sh
│   └── release.sh
│
└── .github/                               # CI/CD
    ├── workflows/
    │   ├── ci.yml
    │   ├── cd-dev.yml
    │   ├── cd-staging.yml
    │   ├── cd-production.yml
    │   └── security-scan.yml
    └── PULL_REQUEST_TEMPLATE.md
```

---

## 3. 关键目录说明

### 3.1 `contracts/`

所有跨服务接口契约的单一事实来源。任何接口变更必须先修改 Schema，再生成/更新客户端代码。建议使用 JSON Schema/OpenAPI/AsyncAPI，并在 CI 中做兼容性检查。

- `a2a/`：Agent Card、任务请求/响应、能力声明。
- `mcp/`：工具注册表、工具输入输出 Schema。
- `api/`：北部 API（OpenAPI）与异步事件（AsyncAPI）。
- `data/`：诊断状态、证据、结果、设备元数据等数据模型。

### 3.2 `apps/orchestrator/`

LangGraph 单图编排服务，是平台唯一流程入口。目录内按图定义、节点、边、检查点、策略拆分：

```text
apps/orchestrator/src/
├── graph/
│   ├── builder.py          # 图组装
│   ├── state.py            # DiagnosisState 定义
│   ├── nodes/
│   │   ├── task_intake.py
│   │   ├── plan_diagnosis.py
│   │   ├── retrieve_knowledge.py
│   │   ├── query_sensor_data.py
│   │   ├── detect_anomaly.py
│   │   ├── generate_hypotheses.py
│   │   ├── verify_evidence.py
│   │   ├── diagnose.py
│   │   ├── maintenance_decision.py
│   │   ├── generate_report.py
│   │   ├── human_approval.py
│   │   └── knowledge_feedback.py
│   └── edges/
│       ├── conditions.py
│       └── routers.py
├── checkpointer/
├── policies/
│   ├── retry.py
│   ├── timeout.py
│   └── budget.py
└── main.py
```

### 3.3 `apps/agents/`

10 个核心 Agent 各自独立目录，遵循统一结构：

```text
apps/agents/a06_fault_diagnosis/
├── src/
│   ├── agent.py            # Agent Card 与主逻辑
│   ├── prompts/            # 提示词模板
│   ├── tools/              # 该 Agent 允许调用的 MCP 工具声明
│   ├── schemas/            # 输入输出 Schema
│   ├── policies/           # 超时、重试、降级策略
│   └── main.py             # A2A 服务入口
├── tests/
│   ├── unit/
│   ├── contract/
│   └── fixtures/
├── Dockerfile
└── README.md
```

### 3.4 `apps/mcp-servers/`

每个 MCP Server 封装一类工具能力，统一提供 `/healthz`、`/tools`、`/invoke` 和审计埋点。新增工具时：

1. 在 `contracts/mcp/` 新增 Schema；
2. 在 `apps/mcp-servers/` 新增或扩展 Server；
3. 在 `contracts/mcp/tool-registry.yaml` 注册；
4. 运行契约测试与权限测试；
5. 无需修改 LangGraph 编排逻辑。

### 3.5 `services/`

领域服务承担较重业务逻辑，供 Agent/MCP 工具调用，不直接面向用户。例如文档解析服务负责 OCR、结构化切块和向量化，时序服务负责时序查询和特征计算。

### 3.6 `ml/`

算法工程目录，区分数据、训练、评估、提示词和模型卡片。**真实工业数据不得提交到 Git**，只允许提交脱敏样例、数据字典和生成脚本。

### 3.7 `infra/`

部署与环境配置。Kubernetes 采用 base + overlays 模式管理 dev/staging/production 环境差异；密钥通过 KMS/Secret Manager 注入，不进入仓库。

---

## 4. 命名规范

| 类型 | 规范 | 示例 |
| --- | --- | --- |
| 目录/文件 | 小写蛇形，服务目录可带业务前缀 | `knowledge_retrieval`, `document_search_server` |
| Python 模块/函数 | 小写蛇形 | `retrieve_evidence` |
| Python 类 | 大驼峰 | `DiagnosisState` |
| TypeScript 组件 | 大驼峰 | `DiagnosisReport` |
| 接口路径 | 小写中划线/复数 | `/api/v1/diagnosis-tasks` |
| 事件主题 | `iip.<domain>.<event>` | `iip.diagnosis.completed` |
| MCP 工具 | `domain.action` | `document.search` |
| A2A 能力 | `domain.action` | `knowledge.retrieve` |
| 环境变量 | 大写下划线，前缀 `IIP_` | `IIP_LLM_BASE_URL` |
| 数据库表 | 小写蛇形，复数 | `diagnosis_tasks` |
| 容器镜像 | `<registry>/<project>/<service>:<version>` | `registry/iip/orchestrator:1.0.0` |

---

## 5. 分支与版本策略

### 5.1 Git 分支

| 分支 | 用途 | 生命周期 |
| --- | --- | --- |
| `main` | 生产就绪代码 | 永久 |
| `develop` | 集成开发分支 | 永久 |
| `release/*` | 发布准备 | 每个版本 |
| `feature/*` | 功能开发 | 合并即删 |
| `bugfix/*` | 缺陷修复 | 合并即删 |
| `hotfix/*` | 生产紧急修复 | 合并即删 |
| `docs/*` | 文档变更 | 合并即删 |

### 5.2 版本号

采用语义化版本 `MAJOR.MINOR.PATCH`：

- MAJOR：不兼容的接口/架构变更；
- MINOR：向后兼容的功能新增；
- PATCH：向后兼容的缺陷修复；
- 预发布版本使用 `-rc.N`，如 `1.0.0-rc.1`。

### 5.3 变更管理

- 所有代码变更通过 Pull Request，至少 1 名模块负责人 + 1 名测试/安全评审。
- 接口 Schema 变更必须更新 `contracts/` 并通过契约兼容性测试。
- 数据库变更通过迁移脚本管理，禁止手工改生产库。
- 模型、提示词、知识库版本化，发布需附评测报告。

---

## 6. 环境配置

| 环境 | 用途 | 数据 | 部署方式 | 访问控制 |
| --- | --- | --- | --- | --- |
| local | 本地开发 | 脱敏样例/Mock | Docker Compose | 开发者本机 |
| dev | 集成开发 | 脱敏数据 | K8s Dev | 研发内网 |
| staging | 预发布验证 | 脱敏/影子数据 | K8s Staging | 项目组 + 业务代表 |
| production | 生产 | 真实工业数据 | K8s 高可用 | 最小权限 + 审计 |
| sandbox | 算法评测 | 离线数据集 | 独立集群/命名空间 | 算法团队 |

**环境差异管理**：使用 `infra/kubernetes/overlays/<env>` 管理副本数、资源、域名、外部依赖地址和功能开关；敏感配置通过 Secret/KMS 注入。

---

## 7. CI/CD 流水线建议

```text
代码提交
  → 静态检查（ruff/eslint/mypy/tsc）
  → 单元测试 + 覆盖率
  → 契约测试（A2A/MCP/OpenAPI Schema）
  → 构建镜像（SBOM + 签名）
  → 集成测试（Mock 数据源）
  → 安全扫描（SAST/依赖/镜像/密钥）
  → 部署 dev
  → 端到端 Smoke Test
  → 部署 staging
  → 性能/回归/评测
  → 发布审批
  → 灰度部署 production
  → 观察指标与回滚
```

---

## 8. 代码质量门禁

| 类别 | 工具/规则 | 门禁 |
| --- | --- | --- |
| Python 格式 | ruff/black | 无格式错误 |
| Python 类型 | mypy/pyright | 关键模块无类型错误 |
| 前端 | eslint/prettier/tsc | 无错误 |
| 单测覆盖率 | pytest/vitest | 核心模块 ≥ 80% |
| 契约测试 | schemathesis/json-schema | 100% 通过 |
| 安全扫描 | bandit/trivy/semgrep | 无高危 |
| 依赖扫描 | Dependabot/Snyk | 无高危未豁免 |
| 镜像 | 非 root、最小基础镜像、SBOM | 符合基线 |
| 文档 | markdownlint | 无严重错误 |

---

## 9. 工程目录落地检查清单

- [ ] 所有服务具备 `README.md`、`Dockerfile`、健康检查、配置说明。
- [ ] A2A/MCP 接口 Schema 已在 `contracts/` 定义并通过校验。
- [ ] `apps/orchestrator` 是唯一诊断流程入口，无旁路调用。
- [ ] 每个 Agent 有独立测试集、评测集和降级策略。
- [ ] 真实数据、密钥、证书未进入 Git 仓库。
- [ ] CI 包含 lint、单测、契约、安全扫描。
- [ ] 部署清单支持 dev/staging/production 差异化和回滚。
- [ ] 文档与代码版本同步更新。
