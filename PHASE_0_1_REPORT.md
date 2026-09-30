# Phase 0 / Phase 1 交付记录

日期：2026-09-30（Asia/Shanghai）

## 范围与阶段

完整阅读 MASTER_PROMPT.md、FIRST_CODEX_PROMPT.md 和全部项目文档后实施。
初始目录仅有 13 份 Markdown 和 .env.example，没有代码或 Git 仓库。

- Phase 0：初始化前后端、PostgreSQL、开发配置、Git 与启动说明。
  后端 pytest 1 passed、ruff 通过、前端 lint/build 通过，
  前后端 HTTP 返回正常且 PostgreSQL healthy 后进入 Phase 1。
  独立提交：ffd453f。
- Phase 1：用户模型、可撤销 session、登录/me/logout、账号 CLI、
  Alembic 初始 migration、登录页、受保护工作台。
- Phase 2 尚未开始，必须用户确认后继续。

## 技术选择

保持 Vue 3 / Vite / TypeScript / Element Plus / Pinia / Vue Router / Axios，
以及 Python 3.12 / FastAPI / SQLAlchemy 2 / Pydantic / Alembic / PostgreSQL。
数据库 session 符合文档允许的 JWT/session 选项，
新增 auth_sessions 表用于会话过期与服务端撤销；只迁移本阶段的两张表。
密码使用 Argon2；HttpOnly + SameSite=Strict Cookie；写请求校验自定义头与 Origin。
没有引入任何图片 Provider、AI 模特 CRUD 或后续阶段的业务。

## 本机环境

| 项目 | 实际情况 |
| --- | --- |
| 系统 Node / npm | 20.18.3 / 10.8.2，部分最新依赖要求更高 Node |
| 系统 Python | 3.11.8，低于项目要求 |
| 项目 Node | 22.23.3，位于 .tools/node |
| 项目 Python | 3.12.14，位于 .tools/python；backend/.venv |
| Docker | 29.7.2，Compose 5.4.0 |
| 数据库 | PostgreSQL 17 容器，healthy |
| 本次运行方式 | 本机前后端 + Docker PostgreSQL |

本次 Docker Hub 认证端点连接超时，因此未完成前后端镜像构建。
没有用 SQLite 替代 PostgreSQL，也没有把本机 Python 3.11 当作符合要求。

## 最终验证

| 检查 | 实际结果 |
| --- | --- |
| 后端 pytest | 22 passed |
| 后端 ruff | All checks passed |
| Alembic upgrade head | 成功 |
| Alembic check | No new upgrade operations detected |
| 独立 schema migration upgrade / check / downgrade | 通过，包含在 pytest 中 |
| 前端 lint | 通过，无 lint 错误或警告 |
| 前端 TypeScript + Vite build | 通过 |
| Edge 浏览器验收 | 4 passed |
| npm 依赖审计 | 0 vulnerabilities（安装时结果） |
| 实际登录、刷新、退出、退出后重访 | 通过 |
| 错误凭据、表单校验、服务故障提示 | 通过 |
| 390px 手机视口 | 无横向溢出 |
| 桌面/手机截图 | 已查看 |

浏览器初次验收发现测试选择器同时匹配多个表单 alert，
已改为精确匹配凭据错误提示并重新运行，最终全部通过。
最终后端测试保留一条上游 Starlette 关于 httpx TestClient 的弃用提示；
不影响当前测试结果，没有隐藏该提示。

截图保存在 storage/qa/，不提交 Git。
本地端口为 5173 / 8000 / 5432，均只绑定回环地址。

## 账号与使用

- 当前管理员：creator@example.com。
- 随机密码只保存在 .env 的 ADMIN_PASSWORD。
- 数据库只保存密码哈希；不会提交 .env。
- 启动、停止、新账号创建和环境复现命令见 README.md。
- 没有注册接口，没有演示用明文默认密码。

## 剩余事项与下一阶段

唯一未实测的启动方式是完整 Docker 前后端镜像构建，原因是 Docker Hub 网络超时。
当前本机运行方式已经完成登录闭环，服务保持运行。

下一阶段建议按原计划实施 Phase 2：AI 模特基础信息 CRUD 与参考图片上传，
届时再实施上传类型/大小校验和用户数据隔离。当前未开始。

## 文件清单

修改的原有文件：README.md、.env.example。其余原始产品/架构文档保持原样。

新建并纳入 Git 的文件：

- .gitignore
- backend/.dockerignore
- backend/alembic.ini
- backend/alembic/env.py
- backend/alembic/script.py.mako
- backend/alembic/versions/0001_users_and_sessions.py
- backend/app/__init__.py
- backend/app/api/__init__.py
- backend/app/api/auth.py
- backend/app/cli.py
- backend/app/core/__init__.py
- backend/app/core/config.py
- backend/app/core/database.py
- backend/app/core/security.py
- backend/app/main.py
- backend/app/models/__init__.py
- backend/app/models/user.py
- backend/app/repositories/__init__.py
- backend/app/repositories/users.py
- backend/app/schemas/__init__.py
- backend/app/schemas/auth.py
- backend/app/services/__init__.py
- backend/app/services/auth.py
- backend/Dockerfile
- backend/pyproject.toml
- backend/requirements.lock
- backend/tests/__init__.py
- backend/tests/conftest.py
- backend/tests/test_auth.py
- backend/tests/test_health.py
- backend/tests/test_migrations.py
- compose.yaml
- frontend/.dockerignore
- frontend/Dockerfile
- frontend/eslint.config.js
- frontend/index.html
- frontend/package-lock.json
- frontend/package.json
- frontend/playwright.config.ts
- frontend/src/api/client.ts
- frontend/src/App.vue
- frontend/src/main.ts
- frontend/src/router/index.ts
- frontend/src/stores/auth.ts
- frontend/src/style.css
- frontend/src/types/auth.ts
- frontend/src/views/DashboardView.vue
- frontend/src/views/LoginView.vue
- frontend/tests/auth.spec.ts
- frontend/tsconfig.json
- frontend/vite.config.ts
- scripts/create-local-admin.ps1
- scripts/init-env.ps1
- scripts/npm-local.ps1
- scripts/start-local.ps1
- scripts/stop-local.ps1
- storage/.gitkeep
- PHASE_0_1_REPORT.md

本地生成但忽略的内容：.env、.tools/、backend/.venv/、node_modules/、dist/、storage/ 日志与截图、测试缓存。
