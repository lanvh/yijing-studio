# AI Seed Studio

AI Seed Studio 是一个 AI 虚拟模特与商品种草内容生成平台。

用户可以创建 AI 人物，上传服饰、鞋子、包、首饰、手表等商品，并生成 AI 模特穿戴这些商品的种草图片。

## 当前目标

当前版本是 MVP。

目标不是立即做完整 SaaS，而是验证：

1. AI 人物真实度
2. 人物一致性
3. 商品还原度
4. 内容生产效率
5. 单套内容生成成本

## MVP 用户流程

登录

↓

创建 AI 模特

↓

上传商品

↓

选择人物 + 商品

↓

选择场景 / 风格 / 姿势

↓

生成图片

↓

自动生成文案

↓

筛选图片

↓

下载种草素材包

↓

用户人工发布到内容平台

## 当前不做

自动登录第三方内容平台。

自动发布。

自动养号。

自动互动。

## 长期愿景

AI Model Library

+

Product Library

+

AI Wardrobe

+

Scene Library

+

Pose Library

+

Image Generation

+

Video Generation

+

Copywriting

+

Analytics

最终成为：

AI Fashion Content Studio

## 当前进度：Phase 0 / Phase 1

已完成项目初始化、账号创建、登录、会话查询、退出与受保护工作台。
未开放注册；AI 模特、商品、生成、文案、下载功能尚未实现。
须经用户确认后才进入 Phase 2。

### 实际目录

```text
backend/
  app/
    api/auth.py            登录、当前账号、退出 API
    core/                  配置、SQLAlchemy 会话、安全函数
    models/user.py         用户与会话模型
    repositories/users.py  数据访问
    schemas/auth.py        请求/响应校验
    services/auth.py       认证与账号创建逻辑
    cli.py                 本地创建账号
    main.py                FastAPI、健康检查
  alembic/                 显式数据库 migration
  tests/                   PostgreSQL 认证及 migration 测试
  requirements.lock        后端依赖锁
frontend/
  src/api/                 Axios
  src/router/              登录保护
  src/stores/              Pinia 会话
  src/types/               用户类型
  src/views/               登录页、工作台
  tests/                   浏览器验收
scripts/                   环境初始化、启动、停止、创建账号
storage/                   本地日志、截图；内容不提交 Git
compose.yaml               PostgreSQL、后端、前端开发配置
.env.example               无秘密的环境变量示例
```

### 本机启动（已验证）

本机已经准备好项目专用 Python 3.12.14、Node 22.23.3、后端虚拟环境、
前端依赖和 PostgreSQL 17 容器。不会替换系统 Python / Node。

在项目根目录运行，Docker Desktop 需保持启动：

```powershell
cd D:\AiProject\codex\ai-seed-studio-docs
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

脚本启动数据库，显式执行 `alembic upgrade head`，再以隐藏窗口启动前后端。
应用进程本身不会建表或修改 schema。
启动脚本不会重启已监听端口的进程；代码更改后需停止再启动。
若端口被其他程序占用，请先调整/释放端口。

- 登录：http://localhost:5173/login
- 工作台：http://localhost:5173/dashboard
- API 文档：http://localhost:8000/docs
- 存活：http://localhost:8000/api/v1/health
- 数据库与 schema 就绪：http://localhost:8000/api/v1/health/ready

统一使用 localhost 访问。若更换域名，请同步修改 .env 的 FRONTEND_URL。
日志：storage/backend.log、backend-error.log、frontend.log、frontend-error.log。

停止本项目的前后端进程：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop-local.ps1
docker compose down
```

第二条命令停止数据库且保留数据 volume。不要随意使用 `down -v`，它会删除数据库数据。

### 登录账号

已创建本地管理员：`creator@example.com`。
随机密码保存在根目录 .env 的 `ADMIN_PASSWORD`，请在本地编辑器中查看。
.env 已被 Git 忽略，密码不写入源码或测试文件。数据库只保存 Argon2 密码哈希。
修改 .env 不会更改已有账号的密码。

新增账号（交互输入密码，不回显）：

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.cli create-user --email you@example.com --display-name "你的名字"
```

密码为 12–128 字符。管理员可加 `--role admin`。
账号邮箱按小写保存；重复邮箱明确报错且不覆盖原账号。

在新环境创建随机密码本地管理员：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/create-local-admin.ps1
```

此脚本将随机凭据写入 .env 后调用 CLI，不会覆盖数据库中的已有账号。
创建完账号后可删除 .env 中的 ADMIN_PASSWORD；删除后浏览器自动化测试需另行提供测试凭据。

### 新电脑准备环境

要求 Docker Desktop（Linux containers）、Python 3.12+、Node 22.13+、npm。
如果系统版本偏旧，可按本次采用的方法仅在项目内安装：

```powershell
python -m pip install --target .tools/uv uv
$env:UV_PYTHON_INSTALL_DIR = Join-Path $PWD '.tools/python'
$env:UV_CACHE_DIR = Join-Path $PWD '.tools/cache'
.\.tools\uv\bin\uv.exe python install 3.12
.\.tools\uv\bin\uv.exe venv backend/.venv --python 3.12
.\.tools\uv\bin\uv.exe pip install --python backend/.venv/Scripts/python.exe -r backend/requirements.lock
npm install --prefix .tools/node --no-audit --no-fund node@22
powershell -ExecutionPolicy Bypass -File scripts/npm-local.ps1 ci
powershell -ExecutionPolicy Bypass -File scripts/init-env.ps1
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
powershell -ExecutionPolicy Bypass -File scripts/create-local-admin.ps1
```

已有 Python 3.12+ 时也可以用 `python -m venv backend/.venv`，
再用虚拟环境的 pip 安装 requirements.lock。
npm-local.ps1 优先使用项目的 Node 22，避免 Windows 的系统 npm.cmd 自动选用旧 Node。

### 完整 Docker 开发方式

配置已提供，但本机因 Docker Hub 认证连接超时，前后端镜像未构建成功。
已验证的是上面的“本机前后端 + Docker PostgreSQL”方式。

网络可用后，先停止本机前后端以释放端口，再执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/init-env.ps1
docker compose up -d db
docker compose build backend frontend
docker compose run --rm backend alembic upgrade head
docker compose up -d backend frontend
docker compose exec backend python -m app.cli create-user --email you@example.com --role admin
```

Compose 与 Python 都读取根目录 .env；不要提交该文件。
init-env.ps1 只在 .env 不存在时生成文件，自动填充随机数据库密码。
PostgreSQL 密码初始化后持久化在 volume 内；只改 .env 不会修改数据库已有密码。
修改 compose.yaml 的 POSTGRES_DB/POSTGRES_USER 时也要同步修改 DATABASE_URL。

### 认证接口

统一前缀 /api/v1：

| 方法 | 路径 | 行为 |
| --- | --- | --- |
| POST | /auth/login | JSON email/password；成功返回用户并设置 HttpOnly Cookie |
| GET | /auth/me | 当前用户；无效、过期、停用会话返回 401 |
| POST | /auth/logout | 服务端删除会话并清除 Cookie，返回 204 |
| GET | /health | 进程存活 |
| GET | /health/ready | PostgreSQL 连接与迁移就绪 |

认证采用数据库 session（符合文档 JWT/session 的要求），不需要 JWT Secret。
Cookie 为 HttpOnly、SameSite=Strict，服务端仅保存随机 token 的 SHA-256 哈希；
退出即撤销，重新登录轮换当前 session。会话默认有效期 1440 分钟。
所有写请求必须带 `X-Requested-With: AISeedStudio`；
浏览器 Origin 必须匹配 FRONTEND_URL，Axios 已配置该头。
前端不把凭据放入 localStorage。当前工作台只展示账号和后续功能说明。

本配置仅绑定回环地址，供本地开发使用；尚非生产部署配置。
生产环境应使用 HTTPS、COOKIE_SECURE=true，并在网关配置登录限流。

### 验证命令

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m alembic check
cd ..
powershell -ExecutionPolicy Bypass -File scripts/npm-local.ps1 run lint
powershell -ExecutionPolicy Bypass -File scripts/npm-local.ps1 run build
powershell -ExecutionPolicy Bypass -File scripts/npm-local.ps1 run test:e2e
```

后端测试使用真实 PostgreSQL，每个认证测试使用可回滚事务，migration 测试使用独立临时 schema；
测试前显式升级 schema。仅对本地开发数据库运行。
浏览器测试使用本机 Edge；需先启动服务，并在根目录 .env 提供 ADMIN_EMAIL/ADMIN_PASSWORD。
无 AI API Key 不影响上述启动和验证。详细结果及文件清单见 PHASE_0_1_REPORT.md。
