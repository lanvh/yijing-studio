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

## 当前进度：Phase 0 / Phase 1 / Phase 2

已完成项目初始化、账号创建、登录、会话查询、退出与受保护工作台。
已完成 AI 模特 CRUD 与参考图片管理。未开放注册；商品、生成、文案、下载尚未实现。
本次止于 Phase 2；经用户确认后再进入 Phase 3。

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
前端不把凭据放入 localStorage。当前工作台提供 AI 模特库入口；商品与生成等功能仍未开放。

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
无 AI API Key 不影响上述启动和验证。Phase 0/1 历史记录见 PHASE_0_1_REPORT.md，当前阶段见 PHASE_2_REPORT.md。

## Phase 2：AI 模特库

已实现的页面：

- /models：当前用户的模特库、名称搜索、分页、卡片封面、编辑与删除。
- /models/create：创建成人虚拟模特配置。
- /models/:id：资料详情、参考图上传、预览和移除。
- /models/:id/edit：编辑基础信息；不改变已有参考图。

操作顺序：登录 → AI 模特 → 新建模特 → 保存资料 → 确认参考图来源 → 上传图片。
也可从工作台“新建 AI 模特”进入。未上传图片时显示明确的参考图空状态。

本阶段字段包括名称、性别、成年年龄段、身高、体型、肤色、发型、发色、风格与描述。
仅名称、性别、年龄段必填；身高可留空。数据库保留 character_prompt、
negative_prompt、provider_metadata，当前不调用 Provider 或构造生成任务。

### 参考图与本地存储

- 支持静态 JPEG / PNG / WebP。扩展名、声明 MIME 与解码后的实际格式必须一致。
- 默认每张最多 15 MiB、2400 万像素，每条边 32–8192 像素，每个模特最多 8 张。
- 服务端限制整个上传请求大小（包含未提供 Content-Length 的分块请求），再校验文件。
- Pillow 完整解码、修正 EXIF 方向、去除元数据后保存 JPEG；透明背景合成为白色。
- 第一张参考图作为封面；移除第一张后，下一张自动成为封面。
- 存储键为 models/<用户 UUID>/<模特 UUID>/<图片 UUID>.jpg，
  不使用原始文件名，也不接受客户端指定存储路径。
- 开发环境默认保存在项目根目录 storage/models/。
  LOCAL_STORAGE_PATH 相对项目根目录解析；Compose 明确指定 /app/storage 并挂载根目录 storage/。
- 图片通过带登录验证的 API 返回，未挂载公开的 /storage 静态目录。
  数据查询、编辑、删除和图片读取均强制检查所属用户，管理员也不绕过所有权。
- 文件写入失败不写入图片记录；数据库提交失败则清理新文件。
  删除时先提交数据库，再清理文件。若磁盘删除失败，会记录服务端错误；
  遗留文件不可通过 API 访问，需要根据日志清理。文件系统与数据库不支持跨资源原子事务。

.env 可配置 MAX_IMAGE_SIZE_MB、MAX_IMAGE_PIXELS、MAX_MODEL_IMAGES、
ALLOWED_IMAGE_TYPES、LOCAL_STORAGE_PATH，重启后生效。
现有 .env 没有新字段时采用上述默认值。界面从 /models/options 读取上传限制。

### 来源与审核边界

上传前需要确认图片为有使用权的 AI 虚拟成人形象，非真人照片。
确认时间、声明、原始与保存后内容哈希写入图片 metadata。
ReferenceUploadPolicy 为后续内容审核保留调用点，当前只有声明检查；
没有自动 NSFW、真人识别或年龄识别能力，metadata 如实记录 moderation_status=not_screened。

### 升级与验证

安装新增依赖后重启（请在项目根目录执行）：

```powershell
.\.tools\uv\bin\uv.exe pip install --python backend/.venv/Scripts/python.exe -r backend/requirements.lock
powershell -ExecutionPolicy Bypass -File scripts/stop-local.ps1
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

启动脚本显式执行 migration 0002，新增 ai_models 与 ai_model_images，不改变已有登录账号。
测试命令继续使用上面的 pytest、ruff、alembic check、前端 lint/build/test:e2e。
浏览器验收使用合成图片，完成后清理它自己创建的测试模特和图片，
不会把测试占位图当作真实生成结果。验收截图在 storage/qa/phase2-*.png。

详细改动、结果与边界见 PHASE_2_REPORT.md。
下一阶段是 Phase 3 商品 CRUD，本次未开始。
