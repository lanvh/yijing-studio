# REST API

Base URL:

/api/v1

## Auth

POST /auth/login

GET /auth/me

POST /auth/logout

## AI Models

GET /models

POST /models

GET /models/{id}

PATCH /models/{id}

DELETE /models/{id}

POST /models/{id}/images

POST /models/{id}/generate-reference

## Products

GET /products

POST /products

GET /products/{id}

PATCH /products/{id}

DELETE /products/{id}

POST /products/{id}/images

POST /products/{id}/analyze

## Generation

POST /generation/tasks

GET /generation/tasks

GET /generation/tasks/{id}

POST /generation/tasks/{id}/retry

DELETE /generation/tasks/{id}

## Results

GET /generation/tasks/{id}/results

PATCH /generation/results/{id}

DELETE /generation/results/{id}

## Copy

POST /generation/tasks/{id}/copy

GET /generation/tasks/{id}/copy

## Export

POST /generation/tasks/{id}/export

GET /generation/tasks/{id}/export

## System

GET /health

GET /providers
## Phase 2 实现约定

本节描述当前实现；前述后续阶段端点暂未开放。

- GET /models 返回 {items, total, limit, offset}。
  支持 q（名称包含搜索）、limit（1–100，默认 24）、offset（默认 0）。
- POST /models、GET /models/{id}、PATCH /models/{id}、DELETE /models/{id} 已实现。
  POST 返回 201；DELETE 返回 204；PATCH 仅修改提交的字段。
- GET /models/options 返回 max_image_size_mb、max_image_pixels、
  max_model_images、allowed_image_types。
- POST /models/{id}/images 使用 multipart/form-data，字段为 file 和 rights_confirmed。
  rights_confirmed 必须为 true，含义为声明图片是已获使用权的 AI 虚拟成人形象、非真人照片。
  成功返回 201 及图片 id、image_url、image_type、metadata、created_at。
- GET /models/{id}/images/{image_id} 返回所属用户的规范化 JPEG，Cache-Control: no-store。
- DELETE /models/{id}/images/{image_id} 移除单张参考图，返回 204。
- POST /models/{id}/generate-reference 尚未实现，不在 Phase 2 范围。

所有接口要求有效登录 Cookie；写请求沿用 X-Requested-With: AISeedStudio 和 Origin 校验。
跨用户对象访问与不存在对象统一返回 404；没有管理员跨用户旁路。
未登录返回 401；请求过大 413；格式不匹配 415；字段/内容无效 422；参考图达到上限 409。
客户端不能写入 user_id、character_prompt、negative_prompt 或 provider_metadata。
