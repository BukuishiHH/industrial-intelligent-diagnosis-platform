# IIP 前端控制台（frontend）

> 工业智能诊断平台 · BG-01 设备检修诊断场景的前端
> 技术栈：React 18 + TypeScript + Vite 5 + React Router 6（零 UI 组件库依赖，样式为自研 CSS）

---

## 一、分层架构

依赖方向严格单向：**pages → hooks → services → api → client**；展示组件只接收 props，不发请求。

| 层 | 目录 | 职责 | 不做什么 |
| --- | --- | --- | --- |
| ① 入口/路由 | src/main.tsx、src/App.tsx | 挂载、路由表、登录守卫装配 | 不写业务逻辑 |
| ② 页面 | src/pages/ | 组合 hooks 与组件，决定页面结构 | 不直接调 api / fetch |
| ③ 状态 | src/hooks/ | React 状态与副作用（会话状态机、历史、报告、登录态） | 不拼装 HTTP 细节 |
| ④ 服务 | src/services/ | 业务编排：会话归一化（SessionView）、登录态读写、报告取数 | 不关心 UI |
| ⑤ 接口 | src/api/ | 只负责 HTTP：client.ts 统一处理 token / Result 解包 / 401 | 不含业务判断 |
| ⑥ 展示 | src/components/ | 纯展示组件（结论卡片、证据、步骤、徽章…） | 不发请求、不读 storage |
| ⑦ 基础 | src/types/、src/utils/、src/styles/ | 与后端对齐的类型、格式化、Markdown 渲染、全局样式 | — |

    src/
    ├── main.tsx / App.tsx            入口与路由
    ├── api/        client.ts · auth.ts · diagnosis.ts
    ├── types/      common.ts · auth.ts · diagnosis.ts    （与后端 schemas 一一对应）
    ├── services/   auth.service.ts · diagnosis.service.ts
    ├── hooks/      useAuth · useDiagnosisSession · useHistory · useReport
    ├── components/ layout/ · common/ · diagnosis/ · report/
    ├── pages/      LoginPage · DiagnosisPage · HistoryPage · ReportPage
    ├── utils/      storage.ts · format.ts · markdown.ts
    └── styles/     global.css

### 关键设计说明

1. **会话归一化**：后端返回三种状态（awaiting_clarification / awaiting_review / completed），
   services/diagnosis.service.ts 的 toSessionView() 把它们统一成页面可直接渲染的 SessionView，
   页面无需理解后端状态机。
2. **禁止页面直接 fetch**：所有请求经 api/client.ts，token 附加、业务码判断、401 清理集中一处。
3. **登录态只由 auth.service 触碰 localStorage**，便于以后换成后端 session 或刷新 token。
4. **Markdown 自研渲染**（utils/markdown.ts）：零依赖，所有文本先 HTML 转义再拼接，
   报告内容按不可信输入处理，无 XSS 风险。
5. **跨域**：开发期由 Vite 代理 /api → http://127.0.0.1:8000（见 vite.config.ts），后端无需改 CORS；
   生产环境由网关统一转发。

---

## 二、启动

前置：后端已启动，且 WSL2 内的向量模型服务可用。

    cd frontend
    $env:npm_config_cache = (Join-Path $PWD '.npm-cache')   # 缓存落到工作区内，避免权限问题
    npm install
    npm run dev            # http://127.0.0.1:5173

| 命令 | 说明 |
| --- | --- |
| npm run dev | 开发服务器（含热更新） |
| npm run typecheck | 仅类型检查（tsc --noEmit） |
| npm run build | 生产构建到 dist/ |
| npm run preview | 预览构建产物 |

> Windows 下 Vite 需要 esbuild 以管道方式启动子进程；若在受限沙箱中运行，需放开该限制，
> 否则会报 spawn EPERM。

---

## 三、页面与交互

| 页面 | 路由 | 说明 |
| --- | --- | --- |
| 登录/注册 | /login | 复用后端 /user/*；用户名 2~12 位、密码 6~16 位 |
| 智能诊断 | /diagnosis | 输入提问 →（澄清）→ 结论卡片 → 确认 → 报告 |
| 诊断历史 | /history | 报告列表（来自数据库），点击查看 |
| 诊断报告 | /report/:reportId | Markdown 渲染 + 打印 + 下载 .md |

诊断交互流程（与后端 LangGraph 图一致）：

1. 提交问题 → 若未指定设备，出现**澄清卡片**（选择 FJ-01/02/03，系统不会猜机组）
2. 诊断完成 → **结论卡片**：一句话结论、处置紧迫度、根因与置信度、备选原因、
   知识依据/数据依据两组证据（每条带定位标识）、处置步骤、安全提示与信息缺口
3. 点击「确认并生成报告」→ 报告落库并展示，可下载
4. 「否定」按钮为后续版本预留（当前禁用）

诊断期间显示阶段提示（意图识别 → 知识/数据检索 → 证据融合推理），单次约 20~40 秒。

---

## 四、演示提示

诊断结果取决于后端激活的数据集（环境变量 SENSOR_DATA_PATH）：

| 数据集 | 预期结论 |
| --- | --- |
| 设备传感器仿真数据_72h_unbalance_fj01.csv | 叶轮积灰结垢致转子不平衡（高置信度，含处置步骤） |
| 设备传感器仿真数据_72h_rub_fj01.csv | 异物进入叶轮与机壳碰磨（紧急停机） |
| 设备传感器仿真数据_72h_watemp_fj03.csv | 油冷却器结垢导致瓦温上升 |
| 设备传感器仿真数据_72h_normal.csv | 未发现明确故障（低置信度，验证不编造结论） |

启动后端时指定数据集：

    $env:PYTHONPATH='.'
    $env:SENSOR_DATA_PATH='data/raw_docs/设备传感器仿真数据_72h_unbalance_fj01.csv'
    & 'D:\Anaconda\python.exe' -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
