# 13 团队分工说明（Team Roles and Responsibilities）

> 文档编号：IIP-TEAM-001  
> 版本：V1.0  
> 状态：占位稿（项目启动会填充）  
> 读者：项目经理、职能负责人、全体项目成员

> **说明**：本文档中人员姓名、角色、投入比例、汇报关系、联系方式、日期、预算等全部使用占位符，由项目经理在项目启动会上与各职能负责人确认后填充，形成正式 RACI 基线。

---

## 1. 团队组织原则

1. **单一负责人**：每项工作流有且仅有一个 Accountable（最终负责人）。
2. **职责清晰**：角色边界、交付物、决策权明确，避免多头管理。
3. **跨职能协同**：产品、业务专家、算法、数据、平台、前端、测试、安全、运维共同参与。
4. **测试与安全左移**：测试和安全从需求阶段介入。
5. **知识共建**：业务专家参与知识库、故障库和评测集建设。
6. **可替换性**：关键角色设置备份人，避免单点依赖。
7. **指标驱动**：每个角色对应可衡量产出与质量指标。

---

## 2. 团队组织架构（占位）

```mermaid
flowchart TB
    PM[项目经理<br/>[PROJECT_MANAGER]]
    PO[产品负责人<br/>[PRODUCT_OWNER]]
    ARCH[技术负责人/架构师<br/>[TECH_LEAD]]
    BIZ[业务专家委员会<br/>[BUSINESS_EXPERTS]]
    QA[测试负责人<br/>[QA_LEAD]]
    SEC[安全负责人<br/>[SECURITY_LEAD]]
    OPS[运维/DevOps 负责人<br/>[DEVOPS_LEAD]]

    PM --> PO
    PM --> ARCH
    PM --> QA
    PM --> SEC
    PM --> OPS
    PO --> BIZ

    ARCH --> AI[AI/算法组<br/>[AI_TEAM]]
    ARCH --> DATA[数据/知识工程组<br/>[DATA_TEAM]]
    ARCH --> PLAT[平台/后端组<br/>[BACKEND_TEAM]]
    ARCH --> FE[前端/产品组<br/>[FRONTEND_TEAM]]

    QA --> TEST[测试组<br/>[TEST_TEAM]]
    SEC --> SECENG[安全工程组<br/>[SECURITY_TEAM]]
    OPS --> INFRA[基础设施组<br/>[INFRA_TEAM]]
```

---

## 3. 角色清单与职责（占位）

| 角色编号 | 角色 | 姓名占位符 | 备份人占位符 | 投入比例 | 主要职责 | 关键交付物 |
| --- | --- | --- | --- | --- | --- | --- |
| R-01 | 项目发起人/指导委员会 | `[SPONSOR_NAME]` | `[SPONSOR_BACKUP]` | `[ALLOCATION]` | 资源决策、范围变更、重大风险决策 | 项目章程、决策记录 |
| R-02 | 项目经理 | `[PROJECT_MANAGER]` | `[PM_BACKUP]` | `[ALLOCATION]` | 计划、进度、风险、沟通、变更、验收 | 项目计划、周报、风险登记册 |
| R-03 | 产品负责人 | `[PRODUCT_OWNER]` | `[PO_BACKUP]` | `[ALLOCATION]` | 需求、优先级、验收口径、业务对齐 | 需求规格、验收标准、产品原型 |
| R-04 | 技术负责人/架构师 | `[TECH_LEAD]` | `[ARCH_BACKUP]` | `[ALLOCATION]` | 架构、技术选型、接口治理、技术风险 | 架构设计、ADR、接口契约 |
| R-05 | 业务专家/领域专家 | `[DOMAIN_EXPERT_1]` 等 | `[DOMAIN_EXPERT_BACKUP]` | `[ALLOCATION]` | 故障机理、SOP、评测标注、复核 | 故障库、评测集、专家意见 |
| R-06 | 知识工程师 | `[KNOWLEDGE_ENGINEER]` | `[KE_BACKUP]` | `[ALLOCATION]` | 文档解析、切块、知识库治理、检索评测 | 知识库、切块规范、评测报告 |
| R-07 | 数据工程师 | `[DATA_ENGINEER]` | `[DE_BACKUP]` | `[ALLOCATION]` | 采集、清洗、时序建模、数据质量 | 数据管道、数据字典、质量报告 |
| R-08 | AI/算法工程师 | `[AI_ENGINEER_1]` 等 | `[AI_BACKUP]` | `[ALLOCATION]` | Agent、提示词、RAG、异常检测、评测优化 | Agent 实现、提示词、评测报告 |
| R-09 | 平台/后端工程师 | `[BACKEND_ENGINEER_1]` 等 | `[BE_BACKUP]` | `[ALLOCATION]` | 编排、A2A/MCP、API、数据服务 | 服务代码、接口文档、单测 |
| R-10 | 前端工程师 | `[FRONTEND_ENGINEER]` | `[FE_BACKUP]` | `[ALLOCATION]` | Web 控制台、报告展示、可视化 | 前端应用、组件库、使用手册 |
| R-11 | 测试工程师 | `[QA_ENGINEER_1]` 等 | `[QA_BACKUP]` | `[ALLOCATION]` | 测试策略、用例、自动化、缺陷管理 | 测试计划、用例、测试报告 |
| R-12 | 安全工程师 | `[SECURITY_ENGINEER]` | `[SEC_BACKUP]` | `[ALLOCATION]` | 安全设计、权限、审计、安全测试 | 安全方案、测试报告、整改单 |
| R-13 | DevOps/运维工程师 | `[DEVOPS_ENGINEER]` | `[OPS_BACKUP]` | `[ALLOCATION]` | CI/CD、部署、监控、备份、应急 | 流水线、部署手册、监控看板 |
| R-14 | 知识管理员/运营 | `[KNOWLEDGE_MANAGER]` | `[KM_BACKUP]` | `[ALLOCATION]` | 知识库运营、案例审核、用户培训 | 运营 SOP、案例评审记录 |
| R-15 | 业务用户代表 | `[BUSINESS_USER_REP]` | `[BUR_BACKUP]` | `[ALLOCATION]` | UAT、场景验证、反馈 | 验收反馈、试点报告 |

> 实际人员可一人多角色、一角色多人，但 Accountable 必须唯一，且必须在正式 RACI 中明确。

---

## 4. RACI 矩阵（占位）

> R = Responsible（执行）、A = Accountable（负责）、C = Consulted（咨询）、I = Informed（知会）。  
> 以下角色编号对应第 3 节，具体人员由项目经理填充。

| 工作项 | R-02 PM | R-03 产品 | R-04 架构 | R-05 专家 | R-06 知识 | R-07 数据 | R-08 AI | R-09 平台 | R-10 前端 | R-11 测试 | R-12 安全 | R-13 DevOps | R-14 运营 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 项目计划与治理 | A/R | C | C | I | I | I | I | I | I | C | I | C | I |
| 需求分析 | A | R | C | C | C | C | C | C | C | C | C | I | C |
| 总体架构 | A | C | R | C | C | C | C | C | C | C | C | C | I |
| 文档知识库 | A | C | C | C | R | C | C | C | I | C | I | I | C |
| 数据接入与治理 | A | C | C | C | C | R | C | C | I | C | C | C | I |
| Agent 与模型 | A | C | C | C | C | C | R | C | I | C | C | I | I |
| 编排与双协议 | A | I | C | I | I | I | C | R | I | C | C | C | I |
| 前端与报告 | A | C | C | I | I | I | C | C | R | C | C | I | C |
| 测试与质量 | A | C | C | C | C | C | C | C | C | R | C | C | I |
| 安全与合规 | A | C | C | I | C | C | C | C | C | C | R | C | I |
| CI/CD 与部署 | A | I | C | I | I | I | I | C | I | C | C | R | I |
| 知识运营 | A | C | I | C | C | I | C | I | I | I | I | I | R |
| 验收与移交 | A | R | C | C | C | C | C | C | C | R | C | C | C |

---

## 5. 各角色详细职责（占位）

### 5.1 项目经理 `[PROJECT_MANAGER]`

- 制定和维护项目计划、里程碑、迭代计划和资源计划。
- 管理范围、进度、成本、质量、风险和变更。
- 组织项目例会、评审、验收和汇报。
- 协调跨团队依赖，升级和解决阻塞。
- 维护项目文档基线和决策记录。
- **汇报对象**：`[PROJECT_MANAGER_REPORTS_TO]`
- **关键 KPI**：里程碑达成率、范围变更可控率、风险闭环率、干系人满意度。

### 5.2 产品负责人 `[PRODUCT_OWNER]`

- 梳理业务痛点、用户角色、业务场景和需求优先级。
- 维护产品 backlog 和验收标准。
- 组织业务方、专家和研发澄清需求。
- 参与 UAT 和上线验收，确认业务价值。
- **汇报对象**：`[PRODUCT_OWNER_REPORTS_TO]`
- **关键 KPI**：需求交付准确率、UAT 通过率、用户采纳率。

### 5.3 技术负责人/架构师 `[TECH_LEAD]`

- 负责总体架构、技术选型、接口契约和技术风险。
- 评审 LangGraph 单图、A2A/MCP 分层、数据模型和安全设计。
- 制定编码规范、工程规范和 ADR。
- 解决跨模块技术难题，指导研发团队。
- **汇报对象**：`[TECH_LEAD_REPORTS_TO]`
- **关键 KPI**：架构评审通过率、关键技术风险闭环率、系统 SLA 达标率。

### 5.4 业务专家/领域专家 `[DOMAIN_EXPERT_*]`

- 提供设备机理、故障模式、诊断 SOP 和判断规则。
- 参与知识库结构、故障库和评测集建设。
- 对 AI 诊断结论进行复核、标注和修正。
- 参与 UAT 和现场试点。
- **汇报对象**：`[DOMAIN_EXPERT_REPORTS_TO]`
- **关键 KPI**：知识贡献量、标注质量、复核及时率。

### 5.5 知识工程师 `[KNOWLEDGE_ENGINEER]`

- 负责 27 份文档的解析、OCR、切块、元数据和版本治理。
- 建设检索评测集，优化召回和 Rerank 策略。
- 维护知识库质量、覆盖率和溯源准确性。
- **汇报对象**：`[KNOWLEDGE_ENGINEER_REPORTS_TO]`
- **关键 KPI**：入库成功率、向量块质量、检索命中率、引用准确率。

### 5.6 数据工程师 `[DATA_ENGINEER]`

- 负责 4 台设备 24 个传感器的数据接入、清洗、对齐、特征和数据质量。
- 建设设备/传感器台账和数据字典。
- 维护时序数据管道、断线补数和质量监控。
- **汇报对象**：`[DATA_ENGINEER_REPORTS_TO]`
- **关键 KPI**：数据完整率、采集延迟、特征正确率。

### 5.7 AI/算法工程师 `[AI_ENGINEER_*]`

- 实现 10 个 Agent、提示词、RAG、异常检测和评测。
- 负责假设—验证推理、证据校验、置信度校准。
- 维护评测集、模型卡片、模型版本和优化闭环。
- **汇报对象**：`[AI_ENGINEER_REPORTS_TO]`
- **关键 KPI**：诊断准确率、Top-3 命中率、幻觉率、拒答准确率、Token 成本。

### 5.8 平台/后端工程师 `[BACKEND_ENGINEER_*]`

- 实现 LangGraph 单图编排、A2A Registry/Gateway、MCP Server/Client。
- 实现 API、数据服务、任务、状态、Checkpoint 和可靠性策略。
- 编写单元/契约测试和接口文档。
- **汇报对象**：`[BACKEND_ENGINEER_REPORTS_TO]`
- **关键 KPI**：任务成功率、接口可用性、P95 延迟、契约测试通过率。

### 5.9 前端工程师 `[FRONTEND_ENGINEER]`

- 实现 Web 控制台、问诊交互、报告展示、证据链、图表和复核界面。
- 优化大表格/大图表性能和可用性。
- 配合 UAT 和用户培训。
- **汇报对象**：`[FRONTEND_ENGINEER_REPORTS_TO]`
- **关键 KPI**：首屏时间、交互成功率、可用性测试通过率。

### 5.10 测试工程师 `[QA_ENGINEER_*]`

- 制定测试策略、计划、用例和自动化框架。
- 执行功能、集成、契约、性能、安全、可靠性测试。
- 管理缺陷、组织回归、输出测试报告。
- **汇报对象**：`[QA_ENGINEER_REPORTS_TO]`
- **关键 KPI**：用例覆盖、缺陷逃逸率、自动化率、测试报告质量。

### 5.11 安全工程师 `[SECURITY_ENGINEER]`

- 负责权限模型、数据安全、模型安全、工具安全和审计设计。
- 执行安全测试、渗透测试、依赖/镜像扫描和合规评审。
- 跟踪漏洞整改，参与应急响应。
- **汇报对象**：`[SECURITY_ENGINEER_REPORTS_TO]`
- **关键 KPI**：高危漏洞清零、安全测试通过率、合规评审通过。

### 5.12 DevOps/运维工程师 `[DEVOPS_ENGINEER]`

- 建设 CI/CD、环境、K8s、监控、日志、备份和应急体系。
- 负责部署、升级、回滚、容量和可用性。
- 参与试运行和生产保障。
- **汇报对象**：`[DEVOPS_ENGINEER_REPORTS_TO]`
- **关键 KPI**：部署成功率、可用性、RTO/RPO、告警响应时间。

### 5.13 知识管理员/运营 `[KNOWLEDGE_MANAGER]`

- 负责知识库日常运营、文档更新、案例审核和权限管理。
- 组织专家评审、用户培训和效果复盘。
- 维护运营 SOP 和知识质量看板。
- **汇报对象**：`[KNOWLEDGE_MANAGER_REPORTS_TO]`
- **关键 KPI**：知识更新及时率、案例回流率、用户活跃度、满意度。

### 5.14 业务用户代表 `[BUSINESS_USER_REP]`

- 代表一线用户参与需求、原型、UAT 和试点。
- 提供真实场景、反馈和采纳意见。
- 参与培训和使用推广。
- **汇报对象**：`[BUSINESS_USER_REP_REPORTS_TO]`
- **关键 KPI**：UAT 通过率、使用率、反馈闭环率。

---

## 6. 关键角色备份与交接（占位）

| 关键角色 | 主责人 | 备份人 | 交接内容 | 交接频率 |
| --- | --- | --- | --- | --- |
| 项目经理 | `[PROJECT_MANAGER]` | `[PM_BACKUP]` | 计划、风险、干系人、决策 | 每周 |
| 架构师 | `[TECH_LEAD]` | `[ARCH_BACKUP]` | 架构、ADR、接口契约 | 双周 |
| 知识工程 | `[KNOWLEDGE_ENGINEER]` | `[KE_BACKUP]` | 解析规则、索引、评测 | 双周 |
| 数据工程 | `[DATA_ENGINEER]` | `[DE_BACKUP]` | 数据管道、台账、质量 | 双周 |
| AI 算法 | `[AI_ENGINEER_1]` | `[AI_BACKUP]` | Agent、提示词、评测 | 每迭代 |
| 平台 | `[BACKEND_ENGINEER_1]` | `[BE_BACKUP]` | 编排、协议、接口 | 每迭代 |
| 安全 | `[SECURITY_ENGINEER]` | `[SEC_BACKUP]` | 权限、审计、安全策略 | 每月 |
| 运维 | `[DEVOPS_ENGINEER]` | `[OPS_BACKUP]` | 环境、CI/CD、监控、Runbook | 每月 |

---

## 7. 团队协作机制（占位）

| 机制 | 频率 | 组织者 | 参与人 | 输出 |
| --- | --- | --- | --- | --- |
| 每日站会 | `[DAILY_TIME]` | `[SCRUM_MASTER]` | 研发/测试 | 阻塞项、计划 |
| 迭代计划会 | 每迭代 | `[PRODUCT_OWNER]` | 全体 | Sprint Backlog |
| 迭代评审会 | 每迭代 | `[PRODUCT_OWNER]` | 全体 + 业务 | 演示、反馈 |
| 架构评审会 | 按需 | `[TECH_LEAD]` | 架构/研发/安全 | ADR |
| 测试例会 | 每周 | `[QA_LEAD]` | 测试/研发 | 缺陷与质量报告 |
| 安全评审会 | 里程碑 | `[SECURITY_LEAD]` | 安全/架构/运维 | 安全结论 |
| 知识评审会 | 每两周 | `[KNOWLEDGE_MANAGER]` | 专家/知识工程 | 知识更新 |
| 项目周会 | 每周 | `[PROJECT_MANAGER]` | 角色负责人 | 周报 |
| 指导委员会 | 每月 | `[SPONSOR_NAME]` | 发起人/PM/PO | 决策 |

---

## 8. 团队能力矩阵（占位）

> 评分建议：1=了解，2=可执行，3=熟练，4=专家。由各职能负责人填写。

| 能力领域 | `[MEMBER_01]` | `[MEMBER_02]` | `[MEMBER_03]` | ... |
| --- | --- | --- | --- | --- |
| 工业设备诊断 | `[LEVEL]` | `[LEVEL]` | `[LEVEL]` | ... |
| LangGraph/Agent | `[LEVEL]` | `[LEVEL]` | `[LEVEL]` | ... |
| RAG/检索 | `[LEVEL]` | `[LEVEL]` | `[LEVEL]` | ... |
| 时序数据分析 | `[LEVEL]` | `[LEVEL]` | `[LEVEL]` | ... |
| 后端/API | `[LEVEL]` | `[LEVEL]` | `[LEVEL]` | ... |
| 前端/可视化 | `[LEVEL]` | `[LEVEL]` | `[LEVEL]` | ... |
| 数据工程 | `[LEVEL]` | `[LEVEL]` | `[LEVEL]` | ... |
| 测试/质量 | `[LEVEL]` | `[LEVEL]` | `[LEVEL]` | ... |
| 安全/合规 | `[LEVEL]` | `[LEVEL]` | `[LEVEL]` | ... |
| K8s/DevOps | `[LEVEL]` | `[LEVEL]` | `[LEVEL]` | ... |

---

## 9. 人员投入计划（占位）

| 角色 | `[SPRINT_0]` | `[SPRINT_1_2]` | `[SPRINT_3_4]` | `[SPRINT_5_6]` | `[SPRINT_7_8]` | `[SPRINT_9_10]` | `[SPRINT_11]` | `[SPRINT_12]` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 项目经理 | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` |
| 产品负责人 | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` |
| 架构师 | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` |
| 业务专家 | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` |
| 知识工程师 | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` |
| 数据工程师 | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` |
| AI 工程师 | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` |
| 后端工程师 | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` |
| 前端工程师 | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` |
| 测试工程师 | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` |
| 安全工程师 | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` |
| DevOps | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` |
| 知识运营 | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` | `[FTE]` |

---

## 10. 团队风险与应对（占位）

| 风险 | 影响 | 概率 | 应对 | 责任人 |
| --- | --- | --- | --- | --- |
| 关键角色单点依赖 | 人员变动导致延期 | 中 | 设置备份人、文档化、交叉培训 | `[PROJECT_MANAGER]` |
| 业务专家投入不足 | 知识/评测质量下降 | 中 | 提前锁定时间、高层支持、明确 KPI | `[PRODUCT_OWNER]` |
| AI 人才不足 | 模型效果不达预期 | 中 | 引入外部专家、招聘、工具提效 | `[TECH_LEAD]` |
| 跨团队沟通不畅 | 返工/延期 | 中 | 接口契约、例会、单点负责人 | `[PROJECT_MANAGER]` |
| 安全/合规介入晚 | 上线受阻 | 中 | 安全左移、评审前置 | `[SECURITY_LEAD]` |
| 运维交接不充分 | 生产事故 | 中 | Runbook、演练、交接清单 | `[DEVOPS_LEAD]` |
| 团队负荷不均 | 倦怠/质量下降 | 中 | 资源平衡、看板管理、迭代回顾 | `[PROJECT_MANAGER]` |

---

## 11. 团队启动会填充清单

- [ ] 确认项目发起人、项目经理、产品负责人、技术负责人。
- [ ] 填充所有 `[MEMBER_NAME_*]`、`[ROLE_*]` 占位符。
- [ ] 确认各角色投入比例和起止时间。
- [ ] 确认汇报关系和决策路径。
- [ ] 确认 RACI 矩阵并签字确认。
- [ ] 确认备份人和交接机制。
- [ ] 确认协作例会、沟通工具和文档地址。
- [ ] 确认团队能力矩阵和培训计划。
- [ ] 确认预算、资源和采购责任人。
- [ ] 形成团队分工基线并纳入项目章程。

---

## 12. 占位符字典

| 占位符 | 含义 | 建议填写人 |
| --- | --- | --- |
| `[PROJECT_MANAGER]` | 项目经理姓名 | 项目发起人 |
| `[PRODUCT_OWNER]` | 产品负责人姓名 | 项目发起人 |
| `[TECH_LEAD]` | 技术负责人/架构师姓名 | 项目发起人 |
| `[DOMAIN_EXPERT_*]` | 业务/领域专家姓名 | 业务负责人 |
| `[AI_ENGINEER_*]` | AI/算法工程师姓名 | 技术负责人 |
| `[BACKEND_ENGINEER_*]` | 平台/后端工程师姓名 | 技术负责人 |
| `[QA_ENGINEER_*]` | 测试工程师姓名 | 测试负责人 |
| `[ALLOCATION]` | 投入比例，如 100%、50% | 项目经理 |
| `[FTE]` | 某迭代人力投入 | 项目经理 |
| `[LEVEL]` | 能力等级 1～4 | 职能负责人 |
| `[DAILY_TIME]` | 每日站会时间 | 项目经理 |
| `[PROJECT_START_DATE]` | 项目开始日期 | 项目经理 |
| `[PROJECT_GO_LIVE_DATE]` | 计划上线日期 | 项目经理 |
| `[PROJECT_BUDGET]` | 项目预算 | 发起人/财务 |
| `[GPU_RESOURCE_PLAN]` | GPU 资源计划 | 技术负责人/运维 |

> 本文档为占位稿，所有实际人员、职责、时间和资源信息以项目启动会确认并签署的正式版本为准。
