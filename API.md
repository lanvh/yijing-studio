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


## Phase 3 实现约定

- GET /products 返回 {items, total, limit, offset}；支持 q（名称或品牌的包含搜索）、
  category（可选，精确匹配）、limit（1–100，默认 24）、offset（默认 0）。
- POST /products 返回 201；GET /products/{id}、PATCH /products/{id} 返回完整商品；
  DELETE /products/{id} 返回 204，并清理关联原图和预览图。
- 支持类别：top、bottom、dress、shoes、bag、necklace、bracelet、ring、watch、hat、other。
- 创建字段：name、category 必填；brand、color、description 选填。
  feature_notes 可包含 material、pattern、logo_description、shape、critical_features。
  这些字段表示用户确认的资料。PATCH 只修改显式提交的字段，嵌套 feature_notes 按字段合并；
  文本用空字符串清空，critical_features 用空数组清空，不接受显式 null。
- 客户端不能写入 user_id、id、product_features、图片路径或分析来源。
- GET /products/options 返回 categories、max_image_size_mb、max_product_images。
- POST /products/{id}/images：multipart 的 file、rights_confirmed=true；
  声明仅指拥有商品图片使用权或已获授权。成功返回 201 和更新后的完整商品。
- 商品响应包含 original_images、processed_images，每次上传各增加一条。
  metadata 中的 pair_id 将两条记录关联，processed 的 original_image_id 指向原图。
- GET /products/{id}/images/{image_id}：原图以 attachment 返回，内容保持上传字节；
  预览图返回方向修正、去元数据、白底合成后的 JPEG。均要求所有权，
  设置 Cache-Control: no-store、X-Content-Type-Options: nosniff。
- DELETE /products/{id}/images/{image_id}：传原图或预览图 ID 均删除整对图片，
  返回 200 和更新后的完整商品，特征中的图片观察同步移除。
- POST /products/{id}/analyze 返回重新整理后的完整商品。
  ProductAnalyzer 当前采用 local_evidence_v1：用户字段 + 全图像素色板，
  保存来源、版本与整理时间；material_guess 始终为 null。
  图片色板含背景，不表示商品主色。不执行 AI 视觉识别、抠图或图片生成。

本阶段继承登录、同源写请求和所有权校验。商品图片默认最多 8 次上传（16 条原图/预览记录）；
格式、像素和文件大小限制复用 Phase 2。错误状态沿用 401/403/404/409/413/415/422/503。


## Phase 4 实现约定

GET /providers 已实现，要求有效登录 Cookie，返回配置中的当前 Provider 状态：

```json
{
  "provider": "mock",
  "available": true,
  "mock": true,
  "requires_api_key": false,
  "operations": ["create_character", "virtual_try_on", "edit_image", "generate_scene", "generate_content_set"],
  "message": "本地 Mock 可用；输出带标记的占位图，不调用 AI。"
}
```

返回 Cache-Control: no-store，不暴露 Key、厂商地址或 .env 内容。
配置了未实现的 Provider 时，接口仍返回 200 状态报告，但 available=false、
operations=[]、requires_api_key=null；应用的登录和商品管理仍可正常使用。
健康检查超时/异常也以 available=false 报告，不表示 Provider 可用。

本阶段尚不开放 /generation/tasks、/models/{id}/generate-reference 或结果下载 API。
本地开发验收使用 python -m app.mock_job；业务任务 REST 接口属于 Phase 5。


## 当前 Mock 工作流接口（Phase 5–8、10、11）

所有下列路径均带 /api/v1 前缀，需要登录。写请求沿用 X-Requested-With 和 Origin 校验。
跨账户一律 404（管理员无旁路），私有响应使用 no-store。

- GET /generation/options：场景、风格、姿势与张数选项。
- POST /generation/tasks：model_id、product_id 必填；scene、style、pose、requested_count
  有默认值；request_key 是可选 UUID（建议客户端提供，保持重试幂等）。
  请求不得指定 provider、prompt、文件路径或 user_id。同步执行后返回 201 和任务；
  生成失败以任务 status=FAILED/PARTIAL 表达，仍保留任务可查看。
- GET /generation/tasks：返回 items、total、offset、limit；可按 status 筛选；
  limit 1–100，默认 24，offset >= 0。
- GET /generation/tasks/{id}：返回摘要、results 和 copy；包含 is_active、can_retry、
  attempt、result_count；model_name/product_name 来自快照，原始对象删除后 ID 可为 null。
- POST /generation/tasks/{id}/retry：PENDING、FAILED、PARTIAL 或租期过期的 PROCESSING
  可重试，最多 3 次尝试，补齐剩余数量。正在执行/已完成/超限返回 409。
- DELETE /generation/tasks/{id}：返回 204，删除任务、关联文案和私有图片。
- GET /generation/tasks/{id}/results：结果数组；metadata.file_check 表示文件检查。
- GET /generation/results/{id}/image：返回私有 JPEG/PNG 原始结果。
- PATCH /generation/results/{id}：仅接收 is_selected 严格布尔值。
- DELETE /generation/results/{id}：返回 204。人工删除不改变任务历史生成状态。
- GET /generation/tasks/{id}/copy：返回文案对象，尚未生成时为 null。
- POST /generation/tasks/{id}/copy：重新生成本地模板草稿，覆盖已有文案。
- PATCH /generation/tasks/{id}/copy：保存完整文案，必传 title（1–200）、
  caption（1–5000）、hashtags（最多 20 条，每条 1–60 字）、
  product_summary（最多 2000）、styling_notes（最多 2000）。
  source 由服务端设置为 user_edited，模板稿为 local_template。
- GET 或 POST /generation/tasks/{id}/export：即时 ZIP 下载；至少选择一张图片并已有文案，
  否则 422。包中包含 01_cover.jpg、后续 NN_image.jpg（PNG 时对应 png 扩展名）、
  title.txt、caption.txt、hashtags.txt、product_summary.txt、styling_notes.txt、
  product.json、manifest.json、README.txt。
  manifest 明确标注 mock=true、real_generation=false、导出数量和逐图文件哈希。

任务资料与参考图存储路径不通过 REST 返回。
Mock 失败注入仅用于本地单元测试，不提供 HTTP 参数或测试后门。
/models/{id}/generate-reference 与真实图片 Provider 仍未开放。
