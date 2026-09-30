# Phase 4 完成报告

日期：2026-09-30。工作分支：codex/phase-4-mock-provider。
起点为 Phase 3 提交 453c668；本阶段完成 Mock Image Provider。

## 完成项

- 异步 ImageProvider Protocol 与严格校验的 GenerationRequest、GenerationSettings、
  ImageReference、ProviderImage、ProviderResult、ProviderError、ProviderHealth。
- 五类操作：create_character、virtual_try_on、edit_image、generate_scene、
  generate_content_set，另提供 health_check。
- Mock 使用现有 Pillow 生成 1、2、4、6 张 JPEG，默认 768×1024；
  每张图有明显 MOCK / PLACEHOLDER 和 NOT AN AI-GENERATED PHOTO 标记。
- ImageService → ProviderRouter → ImageProvider 调用链，配置决定路由；
  未实现的名称明确不可用，不回退为 Mock。
- 支持完整成功、部分失败、全部失败和超时；保留成功图片与统一错误码。
  服务端检查张数、图片 ID、实际格式、尺寸及完整解码。
- GET /api/v1/providers 需登录，不暴露 Key、厂商地址或环境配置。
- 本地命令 python -m app.mock_job 完成请求、路由、生成、结果图片及 manifest 落盘；
  可显式模拟指定图序号失败，写入失败回收本次已写文件。
- Provider job ID 使用字符串兼容未来厂商原生标识；Mock 为每次调用分配独立 UUID 字符串。
- 未安装新依赖；复用现有 Pillow 与私有存储。未新增数据库表或 migration。

## 阶段边界

MILESTONES 的 Phase 4 验收“创建生成任务”与 Phase 5 有重叠。
本阶段以可独立执行的本地 Provider 任务打通无 Key 调用，
保存开发结果清单，尚未建立业务 GenerationTask / GenerationResult 记录。
Phase 5 再实现任务创建 API、状态查询、结果入库与重试；Phase 6 接入创建和结果页面。

Mock 不渲染人物或商品参考图，不执行真实试穿、编辑或场景生成；
只记录参考图数量和哈希。negative_prompt 被接收但不应用，metadata 如实标记。
cost=0，real_generation=false、references_used=false、mock=true。
不应以 Mock 输出评价人物一致性、商品还原度或真实图片质量。
未开发真实 Provider、文案、ZIP 导出或质量评分。

## 验证结果

| 检查 | 实际结果 |
| --- | --- |
| 最终后端完整 pytest | 154 passed（原有 94 项 + 本阶段 60 项） |
| 专项离线运行 | 58 passed；之后新增的厂商 job ID 契约测试已纳入最终完整回归 |
| Ruff | All checks passed |
| 前端 ESLint | 通过 |
| TypeScript + Vite build | 通过 |
| Alembic check | No new upgrade operations detected |
| 数据库当前版本 | 0003 (head) |
| 本地命令实跑 | SUCCEEDED，4/4 JPEG + manifest.json |
| 图片检查 | 768×1024 JPEG 可解码，Mock 标识清晰 |
| 实际 HTTP | 数据库就绪；未登录 /providers 为 401；登录后 Mock 可用、5 类操作 |
| 阶段隔离 | /api/v1/generation/tasks 仍为 404 |

测试覆盖：
所有操作与张数、调用期间阻止网络连接、参数/参考图分组校验、确定性图片、
独立任务/图片标识、部分/全部失败、超时取消、错误信息不泄漏、
无效输出拦截、存储写入回收、CLI 退出码以及接口鉴权和配置。
测试 fixture 调整为只有数据库测试触发 migration，纯 Provider 测试无需 PostgreSQL。

pytest 保留原有的一条 Starlette/httpx 弃用警告。
本阶段前端源码没有修改，因此运行 lint/build；没有再次运行全套浏览器 CRUD 测试。
已验证的是本机 Node/Python + Docker PostgreSQL，完整前后端 Docker 镜像构建仍未验证。

## 如何使用

应用仍从项目根目录运行 scripts/start-local.ps1。
已有应用代码更新后，先运行 scripts/stop-local.ps1 再启动。
前端：http://localhost:5173
API 文档：http://localhost:8000/docs
需登录状态接口：http://localhost:8000/api/v1/providers

在 backend 目录运行：

```powershell
.\.venv\Scripts\python.exe -m app.mock_job --count 4
.\.venv\Scripts\python.exe -m app.mock_job --count 4 --simulate-failure-at 2
```

成功退出码 0；部分/全部生成失败为 2；存储错误为 1。
文件保存到项目 storage/mock_jobs/<UUID>/，不会写入模特库或商品库。
此命令无需 PostgreSQL 或第三方 AI Key；现有 .env 提供应有配置即可。

本次实跑结果：
storage/mock_jobs/93d94318-68cf-4a10-82c6-6c0ec444eda3/manifest.json。
同目录保留四张占位图，均被 Git 忽略。
配置 IMAGE_PROVIDER=mock，IMAGE_PROVIDER_TIMEOUT_SECONDS 默认 30 秒。

## 环境排障记录

验证时 Docker Desktop 已停止，启动后日志连续报告两个本地零字节 socket 不可访问。
将仅含 socket 的运行目录改名备份并重启后，原有 PostgreSQL 容器恢复 Healthy。
未重置 Docker，未修改或移除数据库、镜像、虚拟磁盘或凭据内容。

保留的可逆运行时备份位于：
- C:/Users/城玮/AppData/Local/Docker/run.phase4-backup-20260930-192028
- C:/Users/城玮/AppData/Local/Docker/run.phase4-backup-20260930-192326
- C:/Users/城玮/AppData/Local/docker-secrets-engine.phase4-backup-20260930-192422

排障时查阅 [Docker 官方故障排查入口](https://docs.docker.com/desktop/troubleshoot-and-support/troubleshoot/)；
具体修复依据为本机日志中的 socket 错误。
初次完整测试因数据库不可达未能运行，恢复环境后的最终完整回归已通过。

## 文件清单

- .env.example
- API.md
- PHASE_4_REPORT.md
- PROVIDER_DESIGN.md
- README.md
- backend/app/api/providers.py
- backend/app/core/config.py
- backend/app/main.py
- backend/app/mock_job.py
- backend/app/providers/__init__.py
- backend/app/providers/contracts.py
- backend/app/providers/mock.py
- backend/app/providers/router.py
- backend/app/services/images.py
- backend/app/services/mock_jobs.py
- backend/tests/conftest.py
- backend/tests/test_providers.py
