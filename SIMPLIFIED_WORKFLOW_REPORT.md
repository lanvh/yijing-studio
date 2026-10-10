# 简化创作流程改造记录（2026-10-10）

本轮按最新需求替代旧版多字段表单，既有资料和图片仍保留。

## 使用方式

1. 新建模特只填名称和性别，保存后在详情页上传成年 AI 虚拟人物参考图。生成时直接参考脸部、发型、身材和肤色；不根据图片推断精确年龄、身高。
2. 添加衣服只填名称，保存后上传正面、背面和局部图。Seedream 直接参考图片外观；豆包分析最多前 4 张商品预览图，记录颜色、图案、版型等视觉观察。
3. 创建内容的素材区域只有 AI 模特、衣服两个下拉选择框。方向区域提供更多场景、风格、姿势，并允许输入最多 1200 字自定义方向。自定义方向优先于冲突的方向预设，人物身份和衣服外观仍以参考图为准。
4. 文案结合商品视觉观察和最多前 2 张生成图片，采用短标题、少量 emoji、2–3 段外观/搭配/场景短文、4–6 个话题标签的结构，仿照用户提供的穿搭分享截图。未知材质、性能和真实使用体验不会当作已确认事实。

## 当前服务配置

项目根目录 `.env` 保留现有 `IMAGE_API_KEY`，不需要重新输入。图片仍用 Seedream，商品分析和文案改用同一火山方舟账号的豆包服务，不调用 OpenAI。

```dotenv
IMAGE_PROVIDER=seedream
IMAGE_API_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
IMAGE_MODEL=doubao-seedream-5-0-pro-260628
LLM_PROVIDER=ark
LLM_MODEL=doubao-seed-2-1-lite-260915
LLM_API_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
LLM_API_KEY=
```

`LLM_API_KEY` 留空会复用 `IMAGE_API_KEY`。商品上传后的分析、生成后的文案会分别调用方舟文字/视觉模型，按服务商规则计费。设置页仅检查配置，不验证账户权限或余额。

分析失败保留上传图片；自动文案失败保留图片并显示本地回退草稿；手动重生成失败保留原文案。旧商品确认信息与新视觉观察分开保存。没有数据库迁移，自定义方向使用现有任务 JSON 快照。

## 验证

- 后端 pytest：231 项通过，包括精简资料、旧字段保留、自定义方向/幂等、Ark 请求协议、结构化返回、视觉分析及文案失败保护。
- 浏览器：原 20 项中 17 项首轮通过；修正旧断言后，受影响的生成和商品全部 11 项通过。登录和模特 9 项通过。
- 前端 TypeScript/生产构建与 ESLint、后端 Ruff、Alembic 数据库一致性检查通过。
- 桌面与 390px 手机布局截图检查。
- 所有自动化测试使用 Mock/本地服务或 HTTP 模拟，没有消耗真实 API 额度。实际模型权限、人物一致性、衣服还原与文案效果仍需用户用真实素材验收。

官方接口参考：[Chat API](https://docs.volcengine.com/docs/ark/chat-api?lang=zh)、[结构化输出](https://docs.volcengine.com/docs/ark/structured-output-beta?lang=zh)。
