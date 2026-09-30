# 第一次交给 Codex 的执行指令

请完整阅读本项目根目录中的：

MASTER_PROMPT.md
README.md
PRD.md
ARCHITECTURE.md
DATABASE.md
API.md
IMAGE_PIPELINE.md
PROVIDER_DESIGN.md
UI_UX.md
COMPLIANCE.md
MILESTONES.md
TEST_PLAN.md

这些文档是本项目的唯一产品和架构基准。

现在不要一次完成整个项目。

第一步请：

1. 检查当前仓库，如果是空目录则初始化项目。
2. 输出你理解的产品目标。
3. 输出你计划采用的目录结构。
4. 输出 Phase 0 和 Phase 1 将创建/修改的文件。
5. 检查本机已有 Node、npm、Python、Docker、PostgreSQL 等环境。
6. 然后只实现：

Phase 0：项目初始化
Phase 1：登录系统

技术栈必须遵守 MASTER_PROMPT.md。

前端：
Vue 3 + Vite + TypeScript + Element Plus

后端：
FastAPI + SQLAlchemy + PostgreSQL

要求：

- 不要一次开发后面的 AI 生成功能。
- 不允许留下无法运行的伪代码。
- 不允许假装测试通过。
- 每完成一个阶段必须实际运行构建/测试。
- 如果当前电脑缺少依赖，可以安装合理的开发依赖。
- API Key 不存在时不影响 Phase 0/1。
- 所有 Secret 放入 .env，不写入源码。
- 创建 .env.example。
- 创建数据库 migration。
- 更新 README 的本地启动方法。

完成后告诉我：

1. 实际创建了哪些文件
2. 如何启动
3. 测试结果
4. 浏览器访问地址
5. 当前登录账号如何创建
6. 下一阶段建议做什么

在我确认之前，不要继续 Phase 2。