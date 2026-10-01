# Development Milestones

## Phase 0

项目初始化。

完成：

frontend
backend
postgres
docker compose
README

成功标准：

前后端可启动。

## Phase 1

登录。

成功标准：

登录
JWT/session
/auth/me

## Phase 2

AI Model CRUD。

成功标准：

创建人物配置。

上传参考图片。

## Phase 3

Product CRUD。

成功标准：

上传商品。

商品列表。

商品详情。

## Phase 4

Mock Image Provider。

成功标准：

不用任何 AI API Key：

完整创建生成任务。

## Phase 5

Generation Task。

成功标准：

创建任务。

查看状态。

结果入库。

## Phase 6

Generation UI。

成功标准：

创建内容页面真正可用。

## Phase 7

Copywriting。

生成：

标题
正文
标签

## Phase 8

Export。

ZIP 下载。

## Phase 9

Real Provider。

接入一个正式图片服务。

成功标准：

上传真实商品

↓

真实生成图片。

## Phase 10

Quality Checker。

简单版：

图片完整性检查。

未来：

Identity
Product Fidelity
Anatomy
Aesthetic

## Phase 11

MVP Stabilization。

修复：

错误处理

loading

retry

empty state

timeouts

logging

## 当前交付状态（2026-10-01）

用户已授权连续推进，且明确本轮只做 Mock 完整流程。
Phase 0–4：已完成（见历史阶段报告）。
Phase 5–8：任务、界面、本地模板文案、ZIP 导出已实现并验收。
Phase 9：按用户要求暂缓，未接入真实图片服务。
Phase 10：基础图片文件完整性检查已完成；视觉评分未实现。
Phase 11：本轮 Mock MVP 稳定性验收通过（175 后端、17 浏览器测试）。
当前为本机同步 MVP；线上部署、队列、并发容量测试与定时维护仍未实现。
完整边界、启动方法和测试记录见 MOCK_WORKFLOW_REPORT.md。


## 完整 MVP 接入进度（2026-10-01）

用户已将范围扩展为完整项目，按 MASTER_PROMPT 的 MVP 定义继续实施。
Phase 9：OpenAI 官方图片适配及模特生成入口已实现，离线协议/集成验收通过；
缺少 API Key，实际官方出图与真实效果验收仍待完成，不能视为全量上线验收。
Phase 7 补齐 AI 文案，Phase 3 补齐 AI 图片观察建议，人工确认的事实保持独立。
Phase 10/11 继续保留基础文件检查与稳定性测试。用户已选择 OpenAI 官方服务，
本机配置已切换，尚缺 API Key；未发起付费调用。完整记录见 MVP_IMPLEMENTATION_REPORT.md。


## Seedream 更新（2026-10-01）

已接入 Seedream 5.0 Pro，当前本机不调用 OpenAI。原生 2K 竖图、多参考图、
候选并发生成、部分失败重试、参考图保存和 ZIP 来源标记已实现。
后端 222 项测试通过；真实密钥待用户本地填写。详情见 SEEDREAM_REPORT.md。
