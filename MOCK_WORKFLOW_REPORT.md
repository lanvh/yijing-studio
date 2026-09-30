# Mock 完整工作流交付记录

日期：2026-10-01（Asia/Shanghai）
分支：codex/generation-workflow
基线：b350bb7（Phase 4）

## 本轮范围

按用户“直接往后做”授权持续推进，且遵守“暂时只做 Mock 完整流程”。
完成 Phase 5 任务、Phase 6 界面、Phase 7 本地文案、Phase 8 导出、
Phase 10 文件完整性检查与本轮 Phase 11 错误/加载/重试/超时处理。
Phase 9 真实图片服务明确暂缓。未配置或调用外部 AI，不产生图片 API 费用。

## 现在能做什么

登录 → 创建模特和商品资料 → 上传图片 → 选择场景/风格/姿势 →
生成 1/2/4/6 张 Mock → 查看任务 → 预览/选择/删除结果 →
编辑并保存文案 → 下载选中素材 ZIP。

- 创建内容、生成记录、结果详情、系统状态页面已接通；工作台显示真实数量和最近任务。
- 任务保存资料与输入图片快照，原始模特/商品修改或删除不影响旧任务。
- 每类使用前 8 张参考图；私有文件沿用登录和所有权校验。
- 相同 request_key 重复提交返回同一任务；不同参数复用 key 被拒绝。
- 部分成功只补齐缺失数量，保留成功图片、选择状态和人工编辑文案。
- 默认执行租期 120 秒，过期可手动恢复；最多 3 次尝试。旧执行结果不能覆盖新尝试。
- 结果可单图下载；ZIP 包含选中图片、标题/正文/标签、摘要/搭配建议、商品快照和 manifest。
- 文案未保存时禁止导出，并在离开时提醒；下载失败、选择失败等均可继续操作。
- 图片、页面、文案和 ZIP 清单均明确区分 Mock 示意内容。

## 实际文件

后端新增：
- backend/alembic/versions/0004_generation_workflow.py
- backend/app/models/generation.py、schemas/generation.py、api/generation.py
- backend/app/services/generation.py、prompts.py、content_copy.py、quality.py
- backend/tests/test_generation.py

后端调整：main.py 注册路由/错误响应/就绪检查；models/__init__.py 注册模型；
迁移断言更新；旧图片测试按本测试对象计数，避免其他账户或浏览器测试数据干扰；
原来“Phase 5 尚未开放”的断言改为请求校验断言。

前端新增：
- frontend/src/types/generation.ts、api/generation.ts、generation.css
- frontend/src/views/CreateContentView.vue、TasksView.vue、TaskDetailView.vue、SettingsView.vue
- frontend/tests/generation.spec.ts

前端调整：router/index.ts、main.ts、WorkspaceLayout.vue、DashboardView.vue。
文档调整：README.md、API.md、DATABASE.md、TEST_PLAN.md 和本报告。

## 验证

- 后端 pytest：175 项通过；含任务闭环、权限、幂等、文件损坏、部分失败、磁盘失败、
  数据库提交失败、执行租期和过期执行隔离。
- 前端 vue-tsc + Vite 生产构建通过；ESLint、Ruff 检查通过。
- Alembic check 无模型漂移；0004 显式迁移可升降级，保留既有业务数据。
- Playwright：17 项通过；其中 5 项覆盖新增 Mock 工作流与异常恢复，12 项回归已有功能。
- 浏览器测试使用合成参考图，清理自身创建数据；不删除用户资料。
- 已检查 storage/qa/workflow-create-desktop.png、workflow-results-desktop.png
  及移动端截图，布局与 Mock 标记清晰，无横向溢出。
- 后端存在既有 Starlette/httpx 测试客户端弃用提示，未影响通过；未为消除提示更换依赖。

## 执行与数据边界

使用同步 MVP，无队列/后台调度器；FastAPI 同步路由在线程池执行，
Provider 调用期间不占用事务行锁。PROCESSING 租期过后需用户显式重试。
基础文件检查仅验证格式、尺寸、完整解码、大小与哈希。
quality_score=100 表示文件检查通过，四项视觉评分均为 null，不能当作效果评分。
Mock 不执行参考图换装、真人合成或语义视觉生成；文案为模板加人工编辑。

ZIP 在内存生成，不累积服务器压缩包。输入与输出保存到项目 storage/tasks。
数据库和文件系统非跨资源事务；异常路径会清理新文件，硬中断仍可能残留孤立文件。
未实现定时清理、多用户并发容量压测、真实图像审核或部署上线。

## 本机运行恢复

本轮续做时 Docker 因损坏的临时 socket 无法启动，备份两个仅含零字节通信文件的目录后恢复。
未重置 Docker，未删除数据库、镜像或虚拟磁盘。
保留的备份目录：
- C:\Users\城玮\AppData\Local\Docker\run.mock-workflow-backup-20261001-022136
- C:\Users\城玮\AppData\Local\docker-secrets-engine.mock-workflow-backup-20261001-022136

Docker 引擎和 PostgreSQL 已重新启动。若以后再次出现同类故障，应检查 Docker 日志后处理，
不要为运行本项目执行 factory reset。

## 如何使用

打开 http://localhost:5173/create-content，使用原有账户登录。
若需重启，在项目根目录先启动 Docker Desktop，然后执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop-local.ps1
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

新建账户：在 backend 目录运行
`.\.venv\Scripts\python.exe -m app.cli create-user --email you@example.com --display-name "你的名字"`，
按终端提示设置密码；已有账户无需重复创建。Secret 仍只保存在本机 .env，未写入源码。

后续若继续 Mock 产品打磨，可增加素材包历史、显式封面排序、任务队列与孤立文件维护。
真实图片服务必须等用户改变当前 Mock-only 范围后再接入。
