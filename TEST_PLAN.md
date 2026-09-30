# Test Plan

## Backend

pytest

至少测试：

login

model CRUD

product CRUD

generation task

provider mock

export ZIP

permissions

invalid file

## Frontend

至少保证：

npm run build

无 TypeScript error。

## Manual Test

测试人物：

Female Casual

Male Streetwear

商品：

T-shirt

Shoes

Watch

Necklace

Bag

## Important Image Tests

### Shoes

检查：

左右鞋一致

颜色

鞋底

Logo

鞋带

### Clothes

检查：

图案

颜色

领口

袖子

版型

### Watch

检查：

表盘

表带

佩戴方向

### Necklace

检查：

数量

吊坠

长度

### Bag

检查：

Logo

五金

肩带

形状

## MVP Acceptance Test

从新账号开始：

登录

创建 Model

上传 Product

生成内容

查看图片

生成文案

下载 ZIP

必须全流程成功。

## Mock 工作流自动化验收

backend/tests/test_generation.py 覆盖真实 PostgreSQL 任务与本地文件：
1/2/4/6 张、幂等提交、参数校验、所有权、CSRF、缺图、部分失败补齐、重试上限、
执行租期、过期执行结果隔离、输入副本失败回收、结果写入部分失败、提交失败恢复、
删除来源后重试、文案快照/人工编辑、文件损坏、ZIP 清单与内容、删除清理。
图片质量仅验收文件完整性。迁移测试覆盖独立 schema 升降级与 metadata 漂移。

frontend/tests/generation.spec.ts 验收完整网页流程、文案保存与离开提醒、
选择/删除图片、ZIP 下载内容、缺图禁用、服务异常恢复、Mock 状态、
部分成功重试界面、桌面与 390px 手机布局。
部分成功 UI 使用浏览器响应模拟，后端部分失败由真实 Mock Provider 注入测试验证；
不在运行中的 API 暴露失败注入能力。

测试仅断言各自创建对象，不要求业务库为空；不会清理用户已有素材。


## 完整 MVP 接入版验收（2026-10-01）

201 项后端测试、20 项浏览器测试通过。
test_real_providers.py 使用 MockTransport 验证官方 API 请求协议、错误映射、
多图编辑、结构化文案/视觉输出、真实任务来源与 ZIP、模特参考图幂等、AI 失败回退。
新增浏览器测试覆盖参考图生成和预选、缺少 Key 时禁用真实生成、
历史真实任务与当前 Mock 配置无关的来源展示。
tests/global-setup.ts 在任何上传/生成前验证服务为 Mock 与本地文案，避免测试产生外部费用。
以上均不替代有效 Key 下的真实官方出图、成本与效果验收；目前该部分尚未执行。
