# AI Seed Studio

AI Seed Studio 是一个 AI 虚拟模特与商品种草内容生成平台。

用户可以创建 AI 人物，上传服饰、鞋子、包、首饰、手表等商品，并生成 AI 模特穿戴这些商品的种草图片。

## 当前目标

当前版本是 MVP。

目标不是立即做完整 SaaS，而是验证：

1. AI 人物真实度
2. 人物一致性
3. 商品还原度
4. 内容生产效率
5. 单套内容生成成本

## MVP 用户流程

登录

↓

创建 AI 模特

↓

上传商品

↓

选择人物 + 商品

↓

选择场景 / 风格 / 姿势

↓

生成图片

↓

自动生成文案

↓

筛选图片

↓

下载种草素材包

↓

用户人工发布到内容平台

## 当前不做

自动登录第三方内容平台。

自动发布。

自动养号。

自动互动。

## 长期愿景

AI Model Library

+

Product Library

+

AI Wardrobe

+

Scene Library

+

Pose Library

+

Image Generation

+

Video Generation

+

Copywriting

+

Analytics

最终成为：

AI Fashion Content Studio
## 本地开发（Phase 0）

推荐使用 Docker Desktop 的 Linux containers 模式。容器提供 Python 3.12、
Node 22 和 PostgreSQL 17；不依赖本机 Python 版本。前端本机运行建议 Node 22.13+。

在项目根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/init-env.ps1
docker compose up -d --build
```

环境初始化脚本只在 .env 不存在时创建文件，并生成随机数据库密码。
.env 和数据库数据不提交 Git。没有任何 AI API Key 也可以启动。

- 前端：http://localhost:5173
- 后端健康检查：http://localhost:8000/api/v1/health
- API 文档：http://localhost:8000/docs

验证：

```powershell
docker compose exec backend pytest
docker compose exec backend ruff check .
docker compose exec frontend npm run lint
docker compose exec frontend npm run build
```

停止：`docker compose down`（保留数据库 volume）。
此 Compose 配置用于本地开发。
