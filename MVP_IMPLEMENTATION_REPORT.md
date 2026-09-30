# 完整 MVP 接入与验收记录

日期：2026-10-01
分支：codex/complete-mvp
基线：81cd1f4

## 当前结论

按照 MASTER_PROMPT 中“仅开发 MVP，不扩展商业 SaaS”的范围，补齐此前剩余的软件接入。
用户已选择 OpenAI 官方服务，本机 .env 已切换图片与文本 Provider 为 openai。
尚未配置 API Key，因此真实生成当前不可用，未发起任何付费 AI 调用。
**真实官方出图与实际商品/人物效果尚未验收，不能将离线协议测试视为真实服务上线验收。**

## 本轮新增

1. OpenAIImageProvider：
   - 实现 create_character、virtual_try_on、edit_image、generate_scene、generate_content_set。
   - 通过 ImageService → ProviderRouter 调用；业务 API 不直接调用供应商。
   - 人物创建走 Images generations；参考图内容生成走 multipart edits。
   - 参考图按人物/商品分组排序；JPEG/Base64 严格解码、尺寸检查、有限响应体。
   - 官方 HTTPS 地址限定、禁止跳转、不下载任意远端结果 URL、不自动重试付费调用。
   - 认证/限流/拒绝/超时等返回脱敏错误；usage 记录原始用量，未知 cost 保持 null。

2. 模特参考图生成：
   - 模特详情新增生成按钮，支持 Mock 和配置后的 OpenAI。
   - 原创虚拟成人形象提示词；保存参考图片和生成来源。
   - request_key 防重复，同模特活动请求互斥，租期与最新请求隔离防止旧结果覆盖。
   - 参考图上限和所属账户校验；生成后可直接用于内容创建。

3. AI 商品分析：
   - 启用 LLM_PROVIDER=openai 时，在商品图片上传或重新分析后调用视觉理解。
   - 最多前 4 张预览图；报告颜色、图案、Logo 位置、结构、表面外观和不确定点。
   - 观察结果保存为 ai_analysis，始终待人工确认，不覆盖已确认商品资料。
   - 输入在调用期间变更时丢弃过期报告；失败保留上传成功的数据并提供重试提示。

4. AI 文案：
   - Responses API 严格 JSON Schema，生成标题/正文/标签/商品摘要/搭配建议。
   - 只使用用户提供与确认的资料；图片观察建议不当作事实传给文案。
   - 限制无依据使用体验或承诺，保留 AI/Mock 标识；最终需人工审阅。
   - 自动文案失败时保留图片并生成 local_fallback 草稿，页面明确展示来源。
   - 显式重新生成失败不覆盖原稿，并检查并发编辑。

5. 界面与导出：
   - 创建、任务列表、结果与设置页面按配置/历史任务动态显示 Mock 或真实模式。
   - 未配置 Key 时禁用真实生成；配置检测本身不发起付费请求。
   - 模特与商品页快捷进入创建内容，预选对应资料。
   - 工作台增加本周任务（UTC 周一）与成功任务统计。
   - ZIP 增加 Provider、逐图模型、时间和 AI 来源标识。
   - 普通界面不提供密钥输入或暴露原始供应商参数。

## 验证结果

- pytest：201 项通过；切换官方模式并修复异常地址提示后再次全量通过。
- Playwright：20 项通过；新增免费模式前置检查后，参考图生成专项再次通过。
- 前端 vue-tsc + Vite 生产构建通过。
- Ruff、ESLint 通过；Alembic check 无漂移，沿用 0004，无新增 schema 迁移。
- 48 个已安装 Python 包依赖检查通过。
- HTTPX 从开发依赖提升为运行依赖，现有 requirements.lock 已包含相同版本；
  离线锁文件重新解析因本地缓存缺少 python-multipart 元数据未执行成功，
  未改变锁文件版本或安装任何替代依赖。
- 真实服务测试使用 httpx.MockTransport，覆盖请求格式、多参考图、部分坏图、认证、
  限流、超时、安全错误、禁止 URL 下载、结构化输出、AI 文案保留、
  商品建议与人工事实隔离、真实来源 ZIP 元数据。
- pytest 默认强制 Mock/本地模式；Playwright 全局前置检查遇到付费模式直接停止。
- 已核对新增模特生成和配置缺失状态截图，文件在 storage/qa/mvp-*.png。
- 保留既有 Starlette/httpx 测试客户端弃用提示，不影响结果，未为清除提示升级框架。
- 本地服务重启后：后端 ready 与前端设置页均返回 200；服务状态为 openai、
  mock=false，图片与文字可用性均为 false（未配置 Key），符合当前实际条件。
- 本次 Docker 启动遇到损坏的零字节套接字。原目录已保留为
  `run.openai-recovery-20261001-072519` 与
  `docker-secrets-engine.openai-recovery-20261001-072519`；重建后 Docker 正常，未重置数据库。

## 配置与费用

仓库模板默认 IMAGE_PROVIDER=mock、LLM_PROVIDER 空/local，不产生外部 AI 调用费用。
本机已按用户要求设置两项 Provider 为 openai，缺少 Key 时显示配置缺失。
官方图片调用需 IMAGE_PROVIDER=openai 与 IMAGE_API_KEY；
默认 IMAGE_MODEL 为 gpt-image-2.5-sunburst，IMAGE_QUALITY=low。
AI 文案与商品分析需 LLM_PROVIDER=openai，默认 LLM_MODEL=gpt-4.1-mini；
LLM_API_KEY 空时复用图片 Key。全部由服务端 .env 配置；本轮只调整非密钥配置，未写入或提交任何 API Key。

IMAGE_API_TIMEOUT_SECONDS 默认 180；LLM_TIMEOUT_SECONDS 默认 60。
真实内容任务租期默认 480 秒，过期后可显式重试。最多 3 次内容任务尝试；
参考图每模特最多保留 100 个提交标识。网络中断/超时不保证上游未计费。
服务状态只检查配置，不验证余额、模型权限或真实网络可达性。

现有参考资料：
- [官方图片生成](https://developers.openai.com/api/docs/guides/image-generation)
- [Images edits API](https://developers.openai.com/api/reference/resources/images/methods/edit)
- [结构化输出](https://developers.openai.com/api/docs/guides/structured-outputs)
- [视觉理解](https://developers.openai.com/api/docs/guides/images-vision)

## 启动

项目根目录先启动 Docker Desktop，再执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop-local.ps1
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

入口：http://localhost:5173/create-content
设置：http://localhost:5173/settings
账号沿用原有本地账号，不需要重新注册。

## 剩余的真实验收

已选择并配置 OpenAI 官方服务；仍需用户将有效 Key 写入本机 .env 并重启服务。
随后用用户有权使用的素材完成一次真实模特参考图、一组商品图片、AI 文案和 ZIP 验收，
检查真实账户访问、费用用量、人物一致性、商品结构/颜色/Logo，并人工确定可发布性。
目前没有这些实测证据，报告没有将其标记通过。

MVP 文档明确排除的会员计费、自动发布、视频、商业 SaaS 未实现。
当前仍是单机同步 MVP；队列、对象存储和线上容量/效果评估属于后续部署扩展。
