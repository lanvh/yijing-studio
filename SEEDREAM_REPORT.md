# Seedream 接入记录

日期：2026-10-01

## 当前配置

用户已选择 Seedream，图片 Provider 为 seedream；文案与商品资料整理使用 local。
本地 .env 的 IMAGE_API_KEY 已留空，供用户填写新的火山方舟密钥。
未从截图复制密钥，未向 OpenAI 或 Seedream 发起真实生成调用。
旧 OpenAI 适配代码保留兼容历史数据，当前配置不会调用 OpenAI。

## 实现

- 默认模型：doubao-seedream-5-0-pro-260628。
- 官方地址：https://ark.cn-beijing.volces.com/api/v3。
- 文生图与多参考图生成均使用 POST /images/generations、JSON 请求和 Base64 参考图。
- 固定生成 1776×2368 JPEG 竖图，保留原生尺寸，不缩小到原 Mock 的 768×1024。
- Pro 单请求生成一张；1/2/4/6 张候选对应相同数量的并发请求，不自动重试。
- 每次内容生成最多使用按现有顺序排列的前 5 张模特图与前 5 张商品图；
  metadata 记录参考图使用/省略数量，符合 Pro 最多 10 张参考图限制。
- 原生返回图片严格检查尺寸、格式和大小。仅处理 Base64，不下载任意结果 URL。
- 部分失败保留成功结果；手动重试仅补缺失图片，仍可能产生费用。
- 保留供应商 AI 水印，结果与导出标记真实 AI / Seedream 来源。
- 文案和商品分析未接新的文字模型，继续使用本地模板/人工资料，无 OpenAI 调用。
- 设置页展示 Seedream，缺少密钥时明确提示 IMAGE_API_KEY 配置位置。
- 共用有响应大小限制、错误脱敏、禁止重定向的 HTTP 传输层，供应商地址分别校验。
- 无数据库 schema 变化。

## 验证

后端 222 项测试通过，新增 21 项 Seedream 测试，包括数量、参考图顺序、原生尺寸、
认证/限流/超时、坏图、拒绝远端下载、部分成功重试、ZIP 和模特参考图幂等。
Alembic check 无漂移，Ruff、ESLint、vue-tsc 和 Vite 生产构建通过。
本地重启后健康检查与设置页返回 200；图片模式 seedream、文案模式 local，密钥缺失状态准确。
浏览器专项 2 项通过：完整 Mock 生成/文案/ZIP 流程与 Seedream 缺少密钥状态。
真实账户余额、模型开通权限、生成效果仍待用户填写密钥后验证。

## 填写密钥

编辑项目根目录 .env 中已有的 IMAGE_API_KEY= 行：

```dotenv
IMAGE_PROVIDER=seedream
IMAGE_API_KEY=在这里填写新的火山方舟密钥
IMAGE_API_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
IMAGE_MODEL=doubao-seedream-5-0-pro-260628
LLM_PROVIDER=local
```

其余配置已完成。修改密钥后在项目根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop-local.ps1
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

访问 http://localhost:5173/settings 查看配置状态。
“配置就绪”只检查本地配置，不代表已经验证上游权限、余额或网络。
方舟控制台需开通所选 Seedream 模型；不要使用 Seedance 视频模型 ID。

## 官方依据

- [图片生成 API](https://docs.volcengine.com/docs/ark/image-generation-api?lang=zh)
- [Seedream 模型能力与尺寸](https://docs.volcengine.com/docs/ark/seedream-4-0-5-0?lang=zh)
- [模型迁移公告](https://docs.volcengine.com/docs/ark/model-deprecation-notice?lang=zh)
