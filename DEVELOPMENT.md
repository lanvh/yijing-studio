# 开发与实现记录

以下内容包含不同阶段的历史配置；当前推荐 Seedream + Ark，或使用 Mock 无密钥演示。

# 衣镜 Studio

AI 模特与穿搭内容创作工作室。

# AI Seed Studio

> 当前已补齐完整 MVP 的软件接入：Mock/真实图片、模特参考图、AI 分析与文案、素材导出。
> 当前本机已改用 Seedream；在 .env 的 IMAGE_API_KEY 填入新密钥后重启即可。配置见文末“Seedream 当前使用配置”。

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

## 当前进度：Phase 0 / Phase 1 / Phase 2 / Phase 3 / Phase 4

已完成项目初始化、账号创建、登录、会话查询、退出与受保护工作台。
已完成 AI 模特 CRUD、参考图片管理、商品 CRUD、商品图片预览与原图下载。
已完成 Mock Provider 本地调用与多张占位图输出。
未开放注册；业务生成任务、真实图片生成、文案和整套素材导出尚未实现。
本次止于 Phase 4；经用户确认后再进入 Phase 5。

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
前端不把凭据放入 localStorage。当前工作台提供 AI 模特库入口；商品库也已开放，生成功能仍未开放。

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
无 AI API Key 不影响上述启动和验证。Phase 0/1 历史记录见 PHASE_0_1_REPORT.md，Phase 2 历史见 PHASE_2_REPORT.md，Phase 3 历史见 PHASE_3_REPORT.md，当前阶段见 PHASE_4_REPORT.md。

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

Phase 2 引入 migration 0002，新增 ai_models 与 ai_model_images，不改变已有登录账号。
测试命令继续使用上面的 pytest、ruff、alembic check、前端 lint/build/test:e2e。
浏览器验收使用合成图片，完成后清理它自己创建的测试模特和图片，
不会把测试占位图当作真实生成结果。验收截图在 storage/qa/phase2-*.png。

详细改动、结果与边界见 PHASE_2_REPORT.md。
Phase 3 商品 CRUD 已完成，见下文。


## Phase 3：商品库

已实现 /products、/products/create、/products/:id、/products/:id/edit：
商品创建、详情、编辑、删除、名称/品牌搜索、类别筛选、分页、图片预览和原图下载。
支持上衣、下装、连衣裙、鞋履、包袋、项链、手链、戒指、手表、帽子和其他，共 11 类。

操作顺序：登录 → 商品库 → 新建商品 → 保存资料 → 确认图片使用权 → 上传商品图片。
已有登录账号继续使用；首次创建账号沿用上文的 create-user 命令。
保存时自动整理用户提供的特征，上传后增加图片色板，也可点击“重新整理特征”。
材质、图案、Logo、形状与关键细节均来自用户填写；不确定的信息可以留空。
当前没有 AI 商品识别；整图色板包括背景，不能当作商品主色。

商品图片私有存储在 storage/products/<用户 UUID>/<商品 UUID>/，
每次上传保留原文件，并另外保存经过 EXIF 方向修正、元数据清理和白底合成的 JPEG 预览。
原文件可能包含原有元数据，仅通过登录鉴权的下载端点返回。
移除图片会成对清理原图和预览图；删除商品会清理全部关联图片。
上传第二份文件失败或数据库提交失败时回收新文件；删除时先提交数据库再清理文件，
磁盘清理失败会记录日志，API 中不再暴露已删除对象。数据库与文件系统不具备跨资源原子性。
图片未经自动内容审核，metadata 中保留 not_screened 标记。

.env 新增可选 MAX_PRODUCT_IMAGES（默认 8），按原始上传张数计数；
共用 Phase 2 的大小、格式和像素限制。现有 .env 无需改动。
无新增开发依赖，无需 AI API Key。

启动或升级（项目根目录，先启动 Docker Desktop）：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop-local.ps1
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

启动脚本执行 alembic upgrade head，当前迁移 0003 新增 products、product_images，
保留已有用户、模特和参考图。访问 http://localhost:5173/products；
API 文档 http://localhost:8000/docs。验证命令沿用上文。

验收覆盖上衣、运动鞋、手表、项链、包袋；使用明确的合成示意图，
测试结束清理自己创建的商品及图片。桌面与移动截图位于 storage/qa/phase3-*.png。
详见 PHASE_3_REPORT.md。Phase 4 实现见下文。


## Phase 4：Mock Image Provider

已实现统一异步 ImageProvider、MockImageProvider、ProviderRouter、ImageService，
以及需登录的 GET /api/v1/providers。无 API Key、无第三方 AI 网络连接即可生成占位图。
当前用户页面继续使用 Phase 3 的模特库与商品库，创建内容和结果页面按后续阶段实施。

配置：

```dotenv
IMAGE_PROVIDER=mock
IMAGE_PROVIDER_TIMEOUT_SECONDS=30
```

已有 .env 缺少这些字段时采用上述默认值。IMAGE_API_KEY、IMAGE_API_BASE_URL、
IMAGE_MODEL 仍为后续真实 Provider 预留，Mock 不读取这些值。
未知 IMAGE_PROVIDER 不会回退到 Mock，而是返回明确的不可用结果。
本阶段未新增依赖与数据库表，migration 仍为 0003。

### 本地 Provider 任务验收

从项目根目录进入 backend 后运行：

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.mock_job --count 4
```

此命令使用合成参考图，经过 ImageService → ProviderRouter → MockImageProvider，
在项目 storage/mock_jobs/<UUID>/ 保存 4 张 JPEG 和 manifest.json。
命令输出结果清单的 storage key；相对存储路径按项目根目录解析。
它不连接 PostgreSQL、不读取商品/人物数据、不调用第三方 AI，不需要启动前端。
现有 .env 提供应用配置即可。所有占位图都带明显 Mock 标记。

可选 --operation：create_character、virtual_try_on、edit_image、generate_scene、
generate_content_set（默认）。可选 --count：1、2、4、6；--seed 用于重复验证。

用于开发测试的失败模拟：

```powershell
.\.venv\Scripts\python.exe -m app.mock_job --count 4 --simulate-failure-at 2
.\.venv\Scripts\python.exe -m app.mock_job --count 2 --simulate-failure-at 1 2
```

成功退出码为 0；部分/全部生成失败为 2，清单仍保留错误和成功图片；
存储写入失败为 1，并回收本次已经写入的文件。
--simulate-failure-at 仅供本地命令使用，不作为线上请求参数。
这些是 Provider 验收任务，不是已入库的 GenerationTask，也不会出现在任务页面。

### 验证与边界

```powershell
# backend 目录内；以下专项测试不要求 PostgreSQL 运行
.\.venv\Scripts\python.exe -m pytest tests/test_providers.py -k "not status_authentication" -q
# 完整回归仍要求启动 PostgreSQL
.\.venv\Scripts\python.exe -m pytest -q
```

Mock 不执行真实人物创建、试穿、图片编辑或场景生成，仅验证调用与结果交付链路。
没有新增运行依赖，演示文件保存在项目 D 盘 storage 内。
完整实现与验证结果见 PHASE_4_REPORT.md。Phase 5 及之后的当前实现见下文。


## 当前可用版本：Mock 完整工作流（2026-10-01）

已完成 Phase 5–8、Phase 10 基础文件检查，以及本轮 Phase 11 稳定性处理。
依照用户要求，Phase 9 真实图片服务暂缓，不需要 API Key。
上文各 Phase 章节是历史记录，当前入口以本节为准。

1. 登录后，在 AI 模特与商品库中分别创建资料并上传图片。
2. 打开 http://localhost:5173/create-content，选择模特、商品、场景、风格、姿势和 1/2/4/6 张。
3. 提交后进入结果页：预览、选择或删除图片，编辑标题、正文、标签、摘要和搭配建议。
4. 保存文案后下载 ZIP。下载包仅包含选中图片，第一张为封面，另附文案、商品快照与 manifest。
5. 在 http://localhost:5173/tasks 查看历史任务；失败或部分完成可手动重试补齐，最多 3 次尝试。
6. http://localhost:5173/settings 显示当前 Mock 服务状态。

图片是带有明显 MOCK 标记的本地示意图，未渲染参考人物或商品。
文案采用本地模板，只引用已填写的资料，不使用 LLM、不编造试穿体验。
文件检查仅检查解码、格式、尺寸、大小和哈希，不评估人物一致性、商品还原或美观。
结果中的 quality_score=100 仅表示文件检查通过；其余四项视觉评分为 null。

### 启动与升级

项目目录：D:\AiProject\codex\ai-seed-studio-docs。先启动 Docker Desktop，再运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop-local.ps1
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

启动脚本会执行 alembic upgrade head；当前迁移 0004 增加 generation_tasks、
generation_results、content_copy 三张表，保留原有数据。不需要安装新的运行依赖。
.env 与管理员账户继续沿用；创建账户方法见本 README 之前的登录章节。
若 Docker 未运行，启动脚本会报告数据库启动失败；启动 Docker Desktop 后重新执行即可。

### 任务执行与恢复

当前为同步 MVP：请求在线程池中执行，生成前提交任务和 PROCESSING 状态，
生成完成再提交结果；生成期间不持有数据库行锁。
默认超时 30 秒，执行租期为“配置超时 × 2 + 60 秒”，默认 120 秒。
页面离开不删除任务。若进程中断，租期过后可从结果页手动重试，不会自动启动后台队列。
每个任务最多尝试 3 次；部分成功只补齐缺失数量，保留成功图片与已编辑文案。
同一 request_key 的重复提交返回同一任务；更改参数但复用 key 返回 409。
网页一次提交超时后，在参数不变的情况下再次提交沿用同一个 key。

任务持有独立的资料和参考图快照；每类按现有顺序使用前 8 张图。
删除或编辑原始模特/商品，不影响已有任务、重试或导出。
文件保存在 storage/tasks/<用户 UUID>/<任务 UUID>/，受登录与所有权校验保护。
删除任务会清理输入副本、结果与文案。ZIP 在内存中生成，不在磁盘重复留存下载包。
数据库与文件系统不具备跨资源原子性；写入/提交失败会回收本次新文件，
清理失败会写日志，硬中断可能遗留不可公开访问的孤立文件，尚未实现定时清理。
正在执行的任务不能删除/修改结果，过期执行结果不能覆盖新的重试。

### 验证

```powershell
# 在 backend 目录
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m alembic check
# 在项目根目录
backend\.venv\Scripts\ruff.exe check backend
powershell -ExecutionPolicy Bypass -File scripts/npm-local.ps1 run lint
powershell -ExecutionPolicy Bypass -File scripts/npm-local.ps1 run build
powershell -ExecutionPolicy Bypass -File scripts/npm-local.ps1 run test:e2e
```

浏览器测试使用本地 .env 管理员登录及合成图片，结束后清理自己创建的对象。
截图保存在 storage/qa/workflow-*.png。完整交付说明见 MOCK_WORKFLOW_REPORT.md。


## 完整 MVP 接入版（2026-10-01）

在 Mock 闭环基础上，已实现 OpenAI 官方图片 Provider、虚拟模特参考图生成、
AI 商品视觉建议、AI 文案与明确的失败回退；所有功能保留 Mock / 本地模式。
真实 Provider 请求格式和业务链路已由离线传输测试验证。
此段记录之前的 OpenAI 接入；当前已改用 Seedream，以文末配置为准。
此前“只做 Mock / 真实 Provider 暂缓”章节属于历史范围，当前以本节为准。

### 免费本地模式（模板默认，可随时切换）

```dotenv
IMAGE_PROVIDER=mock
LLM_PROVIDER=local
```

不用填写任何 AI Key。模特详情的“生成参考图”也可以生成 Mock 示意参考图，
并在创建内容时使用；本地文案和导出继续可用。Mock 不等于真实换装能力。

### 启用 OpenAI 官方服务

在本机 .env 填写，勿把密钥提交到 Git 或发送到聊天：

```dotenv
IMAGE_PROVIDER=openai
IMAGE_API_KEY=你的图片服务密钥
IMAGE_API_BASE_URL=https://api.openai.com/v1
IMAGE_MODEL=gpt-image-2.5-sunburst
IMAGE_QUALITY=low
IMAGE_API_TIMEOUT_SECONDS=180
LLM_PROVIDER=openai
LLM_API_KEY=你的文本服务密钥
LLM_API_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4.1-mini
LLM_TIMEOUT_SECONDS=60
```

LLM_API_KEY 留空时复用 IMAGE_API_KEY；图片和文字服务可分别启用。
模型名称只在服务端环境配置，普通创作页面不暴露参数。
当前官方适配仅允许 https://api.openai.com/v1，不将密钥转发到任意兼容地址。
图片尺寸沿用 768×1024；默认模型支持该尺寸，自行更换模型时需要确认其尺寸能力。
图片服务用 Images API；商品分析与文案使用 Responses API 结构化输出。

修改配置后执行 stop-local.ps1 和 start-local.ps1。设置页只检查配置，
不会为检测可用性发起付费生成；“配置就绪”不代表账户权限或余额已通过远端验证。
真实调用按供应商实际用量计费；软件不自动重试付费请求，不把失败伪装成 Mock 成功。
不保证按固定单张价格计费；图片输入、输出、文字用量及所选质量共同影响费用。

### 新增入口与行为

- 模特详情 → 生成参考图：生成一张原创虚拟成人形象并保存，最多同时执行一个请求；
  以 request_key 防止同一提交重复生成，使用模型元数据保存执行租期和结果标识。
- 模特 / 商品详情 → 使用该素材创建内容：创建页自动选择对应资料。
- 启用 LLM_PROVIDER=openai 后，商品上传成功或“重新整理特征”会分析最多前 4 张预览图；
  AI 建议单独保存到 product_features.ai_analysis，不覆盖人工确认值。
  商品编辑或图片变更会使旧建议失效；分析失败仍保留上传图片，可手动重试。
- 任务成功后自动生成文案；AI 调用失败则保存 source=local_fallback 的本地草稿，
  页面明确提示回退。手动重新生成失败会保留原文案。
- AI 文案只使用已提供商品资料，AI 视觉建议不当作事实输入文案；
  提示词约束并过滤部分无依据体验/承诺，最终仍需人工核对。
- 结果页面按任务本身显示 Mock / AI 来源，即使当前服务配置改变，也不误标旧任务。
- ZIP manifest 保存 provider、逐图 model、时间、AI/Mock 标识与文件校验信息；
  不包含 API Key、内部文件路径或未经验证的金钱成本。
- 工作台增加本周任务与成功任务；本周从 UTC 周一 00:00 开始。
- 真实任务租期为图片超时 × 2 + 文案超时 + 60 秒；默认 480 秒。
  未执行成功的任务可在过期后显式重试，最多 3 次尝试；重试可能再次计费。

### 验收边界

运行原有验证命令即可。pytest 默认强制 Mock/本地文案，
真实适配测试使用 httpx.MockTransport，不会消费真实 API 额度。
浏览器测试通过全局前置检查强制本地 Mock / 本地文案模式；付费模式下自动停止，不执行上传/生成。
软件代码已补齐 MVP 范围；真实出图、人物一致性和商品还原的人工验收仍需有效 Key、
账户权限和真实素材。详情见 MVP_IMPLEMENTATION_REPORT.md。

参考官方文档：
- [图片生成与参考图编辑](https://developers.openai.com/api/docs/guides/image-generation)
- [结构化输出](https://developers.openai.com/api/docs/guides/structured-outputs)
- [图片理解](https://developers.openai.com/api/docs/guides/images-vision)

## Seedream 当前使用配置（2026-10-01）

当前本机已改用 Seedream，之前 OpenAI 配置章节保留作历史参考。
打开项目根目录 `.env`，只需在现有 `IMAGE_API_KEY=` 后填写新的火山方舟密钥。
不要将密钥写入 `.env.example` 或提交到 Git。

```dotenv
IMAGE_PROVIDER=seedream
IMAGE_API_KEY=
IMAGE_API_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
IMAGE_MODEL=doubao-seedream-5-0-pro-260628
IMAGE_API_TIMEOUT_SECONDS=180
LLM_PROVIDER=local
```

保存后执行 `scripts/stop-local.ps1`、`scripts/start-local.ps1`，再打开设置页。
图片默认 Seedream 5.0 Pro，1776×2368 JPEG，带 AI 水印；
选择 N 张会提交 N 次单图请求，部分成功仍可查看和下载，重试只补缺失数量。
最多使用前 5 张模特图与前 5 张商品图，其余参考图保存在项目中但不发给该模型。
Seedream 只负责图片，文案和商品资料整理暂用本地模板，不调用 OpenAI。
本轮未使用真实密钥，尚未验证账户模型权限与实际生成效果。
完整实现和测试记录见 [SEEDREAM_REPORT.md](SEEDREAM_REPORT.md)。

## 当前简化创作流程（2026-10-10）

最新版本只需填写模特名称和性别、衣服名称，然后上传参考图。创建内容增加场景/风格/姿势预设与自定义方向；文案按穿搭分享截图结构生成。图片仍使用 Seedream，商品视觉分析与文案现在使用 Ark 豆包模型，复用已有 IMAGE_API_KEY。上述早期 local/OpenAI 配置仅供历史参考。当前配置与验证见 [SIMPLIFIED_WORKFLOW_REPORT.md](SIMPLIFIED_WORKFLOW_REPORT.md)。

## iPhone 发布助手（2026-10-11）

创作结果 → 手机发布助手 → 同一 Wi-Fi 下扫码 → 长按保存图片 → 一键复制完整文案 → 得物编辑并发布。二维码一小时有效，可撤销，无需绑定得物账号。启动脚本自动识别局域网地址；防火墙阻止访问时以管理员身份执行 scripts/enable-phone-access.ps1。使用方法和验证边界见 [MOBILE_PUBLISH_REPORT.md](MOBILE_PUBLISH_REPORT.md)。
