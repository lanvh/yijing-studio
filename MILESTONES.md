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
