# Phase 3 完成报告

日期：2026-09-30。工作分支：codex/phase-3-products。
本阶段在 Phase 2 提交 f8bf1ec 上继续，只实现 Product CRUD 与商品图片管理。

## 完成范围

- 新增 products 与 product_images，迁移 0003；通过当前登录用户隔离所有商品和图片。
- 商品库支持名称/品牌搜索、11 类商品筛选、分页、封面、创建、详情、编辑和删除。
- 表单可保存品牌、颜色、描述、材质、图案、Logo、形状与关键细节。
- 每次上传保存原文件及经过方向修正、元数据清理的 JPEG 预览；
  原图通过鉴权的附件下载返回，预览可放大查看。
- 原图与预览成对移除；删除商品清理全部图片。
  第二份文件写入失败或数据库提交失败时回收本次已写入的文件。
- ProductAnalyzer 保存用户已确认信息、整张图片色板、来源和整理时间。
  上传、编辑、删除图片时更新特征，也可手动重新整理。
- 商品库入口已接入桌面/移动导航及工作台；提供 loading、空状态、错误重试和删除确认。

## 已运行验证

| 检查 | 结果 |
| --- | --- |
| PostgreSQL 后端 pytest | 94 passed（含原有 62 项，新增 32 项） |
| Ruff check | 通过 |
| Alembic check | No new upgrade operations detected |
| Alembic current | 0003 (head) |
| 前端 ESLint | 通过 |
| vue-tsc + Vite build | 通过 |
| Edge 完整浏览器回归 | 12 passed（登录 4、模特 4、商品 4） |
| 修正截图等待后的商品回归 | 4 passed |
| 桌面/手机截图检查 | 商品列表、详情和表单可正常显示，390px 无横向溢出 |

后端覆盖全部 11 类、字段校验、嵌套特征更新、来源标记、原图字节保留、
EXIF 清理、配对删除、搜索分页、跨账号权限、CSRF、上传限制、分块请求、
文件写入/数据库提交失败回收。迁移测试包括空库升降级、
已有账号保留、Phase 2 模特和参考图在 0002 → 0003 → 0002 → 0003 后保留。

浏览器验收创建并清理上衣、运动鞋、手表、项链和包袋测试商品；
检查原图下载、刷新持久化、编辑、分类搜索、预览、删除、无效图片及服务错误重试。
合成测试图仅为测试素材，不作为生成结果。
截图在 storage/qa/phase3-*.png（未纳入 Git）。

初次测试因 Docker Desktop 未启动而无法连接数据库，启动后完成上述测试。
pytest 存在一条已有 Starlette/httpx 弃用警告，不影响通过结果。
未新增或升级运行依赖。

## 启动与使用

在项目根目录，先运行 Docker Desktop：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

脚本显式运行 alembic upgrade head。若已有旧服务，先运行 scripts/stop-local.ps1。
商品库：http://localhost:5173/products
API 文档：http://localhost:8000/docs

沿用已有账号，无需重新建用户。需要额外账号时：

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.cli create-user --email you@example.com --display-name "你的名字"
```

命令交互输入密码；Secret 继续放在未跟踪的 .env。
可选 MAX_PRODUCT_IMAGES 默认 8（每次上传对应一份原图及一份预览）。
图片大小、格式、像素限制沿用 Phase 2。

## 当前边界

- 特征整理是用户信息与像素统计，不执行品牌、Logo、图案、材质或结构的 AI 识别；
  未知特征保持为空，material_guess 为 null，图片色板包含背景。
- 未执行抠图或自动内容审核，metadata 如实记录 not_screened。
- 文件与数据库没有跨资源原子事务。删除记录后若文件清理失败会记录日志，
  遗留文件已无法通过 API 访问，需要按日志清理。
- 验证环境为本机 Node/Python + Docker PostgreSQL；完整前后端 Docker 镜像构建仍未验证。
- Phase 4 Mock Image Provider、生成任务、文案和素材包导出均未开始。
  下一阶段须经用户确认。

## 文件清单

- .env.example
- API.md
- PHASE_3_REPORT.md
- README.md
- backend/alembic/env.py
- backend/alembic/versions/0003_products.py
- backend/app/api/products.py
- backend/app/core/config.py
- backend/app/core/upload_limits.py
- backend/app/main.py
- backend/app/models/__init__.py
- backend/app/models/product.py
- backend/app/repositories/products.py
- backend/app/schemas/product.py
- backend/app/services/image_uploads.py
- backend/app/services/product_analyzer.py
- backend/app/services/products.py
- backend/tests/test_migrations.py
- backend/tests/test_products.py
- frontend/src/api/products.ts
- frontend/src/components/ProductCover.vue
- frontend/src/layouts/WorkspaceLayout.vue
- frontend/src/main.ts
- frontend/src/products.css
- frontend/src/router/index.ts
- frontend/src/types/products.ts
- frontend/src/views/DashboardView.vue
- frontend/src/views/ProductDetailView.vue
- frontend/src/views/ProductFormView.vue
- frontend/src/views/ProductsView.vue
- frontend/tests/fixtures/product.png
- frontend/tests/products.spec.ts
