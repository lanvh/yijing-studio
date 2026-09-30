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