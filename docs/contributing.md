## 👨‍💻 团队协作开发指南
本项目为公开GitHub仓库，团队成员通过PR机制协作开发。

### 权限说明
- Maintainer/Owner：管理仓库、合并PR、版本发布
- Write成员：可创建分支、提交PR，**不可直接推送至 main / dev**
- 外部贡献者：Fork仓库后提交PR

### 分支策略
- `main`：稳定发布分支，受保护，仅通过dev合并进入
- `dev`：开发主干分支，所有功能分支合并到此
- 特性分支：`feat/xxx` `fix/xxx` `docs/xxx`，从dev检出

### 开发流程
1. 在 Issues 认领任务
2. 从 `dev` 创建特性分支开发
3. 完成后提交 PR，目标分支为 `dev`，指派Reviewer
4. Review通过后合并至 dev
5. 版本稳定后，dev提PR合并进 main

### Commit规范
采用 Conventional Commits：
`feat: xxx` | `fix: xxx` | `docs: xxx` | `refactor: xxx` | `test: xxx`

### ⚠️ 重要约束
- 严禁提交涉密工业文档、现场原始传感器数据
- 向量库、模型缓存、虚拟环境目录不上传仓库