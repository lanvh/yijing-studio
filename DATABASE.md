# Database Design

## users

id UUID PK

email VARCHAR UNIQUE

password_hash VARCHAR

display_name VARCHAR

role VARCHAR

enabled BOOLEAN

created_at TIMESTAMP

updated_at TIMESTAMP

## ai_models

id UUID PK

user_id UUID FK

name VARCHAR

gender VARCHAR

age_range VARCHAR

height INT

body_type VARCHAR

skin_tone VARCHAR

hair_style VARCHAR

hair_color VARCHAR

style VARCHAR

description TEXT

character_prompt TEXT

negative_prompt TEXT

provider_metadata JSONB

created_at

updated_at

## ai_model_images

id UUID PK

model_id UUID FK

image_url TEXT

image_type VARCHAR

metadata JSONB

created_at

## products

id UUID PK

user_id UUID FK

name VARCHAR

brand VARCHAR

category VARCHAR

color VARCHAR

description TEXT

product_features JSONB

created_at

updated_at

## product_images

id UUID PK

product_id UUID FK

image_url TEXT

image_type VARCHAR

metadata JSONB

created_at

## generation_tasks

id UUID PK

user_id UUID FK

model_id UUID FK

product_id UUID FK

scene VARCHAR

style VARCHAR

pose VARCHAR

requested_count INT

status VARCHAR

provider VARCHAR

provider_job_id VARCHAR NULL

prompt TEXT

negative_prompt TEXT

error_message TEXT

created_at

started_at

completed_at

## generation_results

id UUID PK

task_id UUID FK

image_url TEXT

quality_score FLOAT

identity_score FLOAT

product_score FLOAT

anatomy_score FLOAT

aesthetic_score FLOAT

is_selected BOOLEAN

metadata JSONB

created_at

## content_copy

id UUID PK

task_id UUID FK

title TEXT

caption TEXT

hashtags JSONB

product_summary TEXT

styling_notes TEXT

created_at

## 0004 实现补充

显式迁移 0004_generation_workflow.py 新增上述三张业务表。

generation_tasks 额外包含：
- request_key UUID，与 user_id 联合唯一，用于幂等提交。
- snapshot JSONB：创建参数、模特/商品字段、私有输入副本 key。
- attempt INT、lease_expires_at TIMESTAMPTZ：最多 3 次执行，租期和结果提交隔离。
- model_id/product_id 可空，原始资料删除时 SET NULL，快照保留。
- status 检查约束为 PENDING/PROCESSING/SUCCEEDED/PARTIAL/FAILED；
  requested_count 检查约束为 1/2/4/6。

generation_results 额外包含私有 storage_key，不在响应中返回。
quality_score 只表示文件检查通过；identity/product/anatomy/aesthetic_score 均可空，
当前不计算视觉评分。metadata 保存 Mock、尝试编号、实际 MIME、扩展名和 file_check。
结果的 created_at 在写文件时显式记录，以保持生成顺序，重试输出追加在原结果之后。

content_copy 的 task_id 唯一；title 为 VARCHAR(200)，source 记录 local_template 或 user_edited。
任务删除时 results 和 copy 级联删除；用户 FK 沿用现有策略，不增加跨账户访问权限。
