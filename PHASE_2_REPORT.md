# Phase 2 交付记录

日期：2026-09-30（Asia/Shanghai）
分支：codex/phase-2-models
基线：f1ea22c（Phase 1）

## 完成范围

已重新阅读项目文档并检查当前仓库，沿用现有登录、数据库、构建与测试结构。
本次只实施 Phase 2：

- AI 模特创建、列表、名称搜索、分页、详情、修改和删除。
- 基础信息：名称、性别、成年年龄段、身高、体型、肤色、发型、发色、风格、描述。
- 私有参考图片上传、预览、移除；第一张为封面。
- 模特和图片的查询/变更都绑定当前用户。管理员不具有跨用户访问旁路。
- 身份和 CSRF 依赖提取复用；原有登录接口行为保持兼容。
- 工作台侧栏提取为共享布局，增加模特库入口与手机导航。
- 显式 migration 0002 新增 ai_models、ai_model_images，原有账号保持。
- 新增 Pillow 与 python-multipart，已更新 requirements.lock。
- README、API 文档和本报告同步更新。

未实现 Phase 3 商品、Phase 4 Provider、生成任务、文案、下载功能；
未开放 generate-reference 端点，也未调用任何第三方 AI API。

## 上传与存储

默认支持静态 JPEG / PNG / WebP，每张最多 15 MiB、2400 万像素，
边长 32–8192 像素，每个模特最多 8 张，可通过环境变量调整数量/大小/像素限制。

检查请求体上限、扩展名、MIME、实际格式、完整解码、像素数与帧数。
规范化时修正 EXIF 方向、去除元数据、透明背景合成白色并保存 JPEG。
存储键使用用户/模特/图片 UUID，完全不用用户原始文件名。

图片内容、原始内容的 SHA-256、尺寸、来源声明与确认时间存入 metadata。
来源声明只接受有使用权的 AI 虚拟成人形象，当前不支持真人照片。
ReferenceUploadPolicy 预留未来自动审核接入点，当前仅进行声明校验，
不具有 NSFW、真人或年龄自动识别能力，记录 moderation_status=not_screened。

图片只通过鉴权 API 提供，响应 no-store 和 nosniff，没有公开静态文件目录。
正常删除会移除 DB 记录和对应图片。上传后的 DB 提交失败会清理新文件。
数据库删除后若文件系统清理失败，会保留不可通过 API 访问的孤立文件并记录错误日志；
文件系统与 PostgreSQL 之间没有分布式事务，需要根据日志处理这类磁盘异常。

## 实际验证

| 检查 | 最终结果 |
| --- | --- |
| PostgreSQL 后端 pytest | 62 passed（原有 22 + 新增 40） |
| ruff | All checks passed |
| Alembic upgrade head | 成功，当前 0002 |
| Alembic check | No new upgrade operations detected |
| migration 升级/回滚与旧账号保留 | 通过，包含在 pytest 中 |
| 前端 ESLint | 通过，0 错误/0 警告 |
| TypeScript + Vite build | 通过 |
| Edge 浏览器验收 | 8 passed（原有 4 + 新增 4） |
| git diff --check | 通过 |
| 桌面/390px 手机页面截图 | 已查看，未发现横向溢出 |

新增后端覆盖 CRUD、分页搜索、字段验证、匿名及跨用户拒绝、
原始文件名路径穿越、格式伪装、损坏/空/小图、文件与请求大小、
无 Content-Length 的流式请求、像素与数量限制、来源声明、
EXIF 与方向规范化、图片私有读取、级联删除、DB/磁盘失败清理等。

浏览器实际执行 Female Casual 和 Male Streetwear 配置的创建与编辑，
上传合成测试图片、刷新验证持久化、预览与移除、搜索、取消删除/确认删除，
并回归登录、退出、服务故障提示、表单校验和会话过期跳转。
所有测试模特由用例记录 ID 并在结束时清理，不作为用户真实素材保留。
合成 fixture 明确用于自动化验收，不是 AI 生成结果。

修复记录：预览弹窗回调的 TypeScript 类型错误；Element Plus 测试定位与下拉框交互；
手机详情页图片改为完整显示。修复后重跑并取得上述最终结果。
上游 Starlette 对 httpx TestClient 的一条弃用提示仍存在，未隐藏，不影响测试通过。

## 访问与启动

- 模特库：http://localhost:5173/models
- 新建模特：http://localhost:5173/models/create
- API 文档：http://localhost:8000/docs
- 使用原有账号，密码仍在根目录 .env，未创建新的默认明文密码。
- services 保持运行；重启方式仍为 scripts/stop-local.ps1 / scripts/start-local.ps1。
- 日志、QA 截图和上传内容在 storage/，不提交 Git。
- QA 截图：phase2-library-desktop.png、phase2-detail-desktop.png、
  phase2-detail-mobile.png、phase2-form-mobile.png。

本次验证方式为本机 Node 22 / Python 3.12 + Docker PostgreSQL。
完整前后端 Docker 镜像构建仍沿用 Phase 1 的未验证状态，本次没有重新尝试 Docker Hub。

## 下一阶段

Phase 3：商品 CRUD 与商品图片上传。
必须经用户确认后继续，本次没有提前实现。

## 实现时查阅

- [FastAPI 上传文件](https://fastapi.tiangolo.com/tutorial/request-files/)
- [Pillow 图片安全说明](https://pillow.readthedocs.io/en/stable/handbook/security.html)

## 文件清单

修改：

- .env.example
- API.md
- README.md
- backend/alembic/env.py
- backend/app/api/auth.py
- backend/app/core/config.py
- backend/app/main.py
- backend/app/models/__init__.py
- backend/pyproject.toml
- backend/requirements.lock
- backend/tests/test_migrations.py
- compose.yaml
- frontend/src/api/client.ts
- frontend/src/main.ts
- frontend/src/router/index.ts
- frontend/src/views/DashboardView.vue

新增：

- PHASE_2_REPORT.md
- backend/alembic/versions/0002_ai_models.py
- backend/app/api/ai_models.py
- backend/app/api/dependencies.py
- backend/app/core/upload_limits.py
- backend/app/models/ai_model.py
- backend/app/repositories/ai_models.py
- backend/app/schemas/ai_model.py
- backend/app/services/ai_models.py
- backend/app/services/image_uploads.py
- backend/app/services/moderation.py
- backend/app/storage/__init__.py
- backend/app/storage/local.py
- backend/tests/test_models.py
- frontend/src/api/models.ts
- frontend/src/components/ModelPortrait.vue
- frontend/src/layouts/WorkspaceLayout.vue
- frontend/src/models.css
- frontend/src/types/models.ts
- frontend/src/views/ModelDetailView.vue
- frontend/src/views/ModelFormView.vue
- frontend/src/views/ModelsView.vue
- frontend/tests/fixtures/reference.png
- frontend/tests/models.spec.ts
