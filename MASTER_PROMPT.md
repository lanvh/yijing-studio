# AI Seed Studio - Codex Master Prompt

你现在是本项目的首席软件工程师、产品工程师和技术架构师。

请根据本目录中的全部 Markdown 文档，实现一个可运行的 MVP 产品。

项目名称暂定：

AI Seed Studio
中文名：AI 种草摄影棚

==================================================
一、项目目标
==================================================

这是一个 AI 虚拟模特 + 商品换装 + 种草内容生成平台。

第一阶段主要用于我自己生产得物等内容平台的种草素材。

长期目标是发展成为 SaaS：

- 用户注册
- 创建 AI 模特
- 上传商品
- 生成商品穿搭图片
- 生成种草文案
- 下载整套素材
- 购买会员/点数
- 后续扩展视频生成
- 后续支持不同 AI 图像 Provider

但是：

当前只开发 MVP。

不要一次实现整个商业平台。

==================================================
二、MVP 必须完成的核心闭环
==================================================

用户完成：

1. 登录系统
2. 创建 AI 模特
3. 上传商品图片
4. 选择模特
5. 选择商品
6. 选择场景/风格
7. 创建生成任务
8. 后端调用 Image Provider
9. 返回多张结果图片
10. AI 自动生成标题、正文、标签
11. 用户查看结果
12. 用户下载整套素材

闭环完成。

==================================================
三、当前阶段禁止实现
==================================================

不要：

- 自动登录得物
- 模拟点击得物网页
- 自动发表帖子
- Selenium 自动发内容
- Playwright 自动发内容
- 破解平台接口
- 绕过平台限制
- 自动刷奖励
- 自动点赞
- 自动评论
- 自动关注
- 批量养号
- 流量作弊

平台只生产内容。

最终发布由用户人工完成。

==================================================
四、技术栈
==================================================

Frontend:

Vue 3
Vite
TypeScript
Element Plus
Pinia
Vue Router
Axios

Backend:

Python 3.12+
FastAPI
SQLAlchemy 2.x
Pydantic
Alembic

Database:

PostgreSQL

Task / Queue:

MVP 初期允许同步任务。

但是代码结构必须支持后续：

Redis
Celery / RQ

Storage:

开发环境：

./storage

生产环境预留：

S3
OSS
COS

==================================================
五、AI 架构原则
==================================================

图片模型绝对不能写死在业务代码。

必须设计：

ImageProvider

统一接口。

例如：

create_character()
virtual_try_on()
edit_image()
generate_scene()
generate_content_set()
health_check()

第一版：

只实现一个 Provider。

但是未来必须可以新增：

OpenAIImageProvider
KlingProvider
FluxProvider
ComfyUIProvider
OtherProvider

业务代码禁止直接调用厂商 API。

必须：

业务层
↓
ImageService
↓
ProviderRouter
↓
ImageProvider
↓
具体 Provider

==================================================
六、MVP 页面
==================================================

必须实现：

/login

/dashboard

/models

/models/create

/products

/products/create

/create-content

/tasks

/tasks/:id

/settings

核心页面：

AI 模特管理
商品管理
创建内容
生成结果

==================================================
七、AI 模特
==================================================

一个 AI Model 保存：

id

name
gender
age_range
height
body_type
skin_tone
hair_style
hair_color
style
description

reference_images

character_prompt

negative_prompt

provider_metadata

created_at

要求：

模型生成以后保存参考图片。

未来生成内容时：

尽可能保持：

脸
发型
身材
人物风格

一致。

==================================================
八、商品系统
==================================================

Product：

id

name
brand
category
color
description

original_images

processed_images

product_features

created_at

category 包括：

top
bottom
dress
shoes
bag
necklace
bracelet
ring
watch
hat
other

上传商品以后：

执行 Product Analyzer。

提取：

商品类别
主颜色
品牌（可选）
材质
明显图案
Logo 位置
重要结构
商品描述

保存为 product_features。

==================================================
九、生成任务
==================================================

GenerationTask：

id

user_id
model_id
product_id

scene
style
pose

requested_count

status

provider
provider_job_id

prompt

negative_prompt

error_message

created_at
started_at
completed_at

status：

PENDING
PROCESSING
SUCCEEDED
PARTIAL
FAILED

==================================================
十、生成结果
==================================================

GenerationResult：

id
task_id

image_url

quality_score

identity_score
product_score
anatomy_score
aesthetic_score

is_selected

metadata

created_at

MVP：

评分系统可以先使用简单规则或占位实现。

但接口必须存在。

==================================================
十一、内容生成
==================================================

每次图片任务成功以后：

生成：

title

caption

hashtags

product_summary

styling_notes

要求：

文案不要虚构：

- 商品材质
- 商品性能
- 品牌授权
- 使用体验
- 未提供的数据

不能生成：

“我穿了一周”
“实测非常舒服”

除非用户明确提供真实体验。

==================================================
十二、下载素材包
==================================================

提供：

Download Content Pack

生成 ZIP：

01_cover.jpg
02_fullbody.jpg
03_side.jpg
04_detail.jpg
05_lifestyle.jpg
06_extra.jpg

title.txt
caption.txt
hashtags.txt
product.json

manifest.json

文件数量按实际成功生成结果调整。

==================================================
十三、UI 设计要求
==================================================

整体风格：

现代
简洁
专业
偏 AI 创作工具
深色/浅色均可

参考：

AI Studio
摄影工作台
创作者后台

不要做成传统企业后台。

核心首页展示：

新建内容

AI 模特

商品库

最近任务

生成额度（先显示占位）

==================================================
十四、创建内容页面
==================================================

页面采用步骤式设计：

Step 1
选择 AI 模特

Step 2
选择商品

Step 3
选择内容风格

Step 4
选择场景

Step 5
选择姿势

Step 6
选择生成数量

Step 7
生成

场景预设：

street
mall
mirror
studio
cafe
parking
campus
gym
travel

风格：

dewu
streetwear
minimal
korean
sport
luxury
casual

姿势：

front_standing
side_standing
walking
sitting
mirror_selfie
look_down
detail_pose

==================================================
十五、Provider 配置
==================================================

必须通过环境变量配置。

禁止：

API Key 写入 Git。

示例：

IMAGE_PROVIDER=mock

IMAGE_API_KEY=

IMAGE_API_BASE_URL=

IMAGE_MODEL=

==================================================
十六、Mock Provider
==================================================

非常重要：

首先实现：

MockImageProvider

即使没有任何第三方 AI Key：

整个系统也必须可以启动。

Mock Provider 可以：

复制测试图片

或者生成简单 placeholder。

这样：

前端
后端
数据库
任务
结果
下载

全部可以测试。

完成 Mock 后：

再开发真实 Provider。

==================================================
十七、开发原则
==================================================

每次开发：

不要一次写全部代码。

按阶段提交。

阶段完成以后：

运行：

backend tests
frontend build
lint

确认成功。

如果出现错误：

先修复。

不要留下：

TODO critical
fake imports
未实现函数
无法启动代码

==================================================
十八、安全
==================================================

所有上传：

检查：

扩展名
MIME
文件大小

图片重新命名。

禁止使用用户原始文件名直接作为服务器路径。

需要预留：

内容安全审核
真人肖像保护
未成年人保护
NSFW 检测
商品版权确认

==================================================
十九、数据库
==================================================

使用 Alembic migrations。

禁止程序启动时自动随意修改数据库 schema。

提供：

initial migration。

==================================================
二十、代码结构
==================================================

建议：

backend/

app/
  main.py

  api/
  models/
  schemas/
  services/
  providers/
  repositories/
  core/
  storage/
  tasks/

frontend/

src/

  api/
  components/
  layouts/
  views/
  stores/
  router/
  types/

==================================================
二十一、开发顺序
==================================================

严格按照：

Phase 0
初始化项目

Phase 1
用户 + 登录

Phase 2
AI 模特 CRUD

Phase 3
商品 CRUD

Phase 4
Mock Image Provider

Phase 5
生成任务

Phase 6
结果页面

Phase 7
文案

Phase 8
ZIP 下载

Phase 9
真实 Image Provider

Phase 10
质量检测

不要跳阶段。

==================================================
二十二、每次开始编码前
==================================================

首先：

阅读：

README.md
PRD.md
ARCHITECTURE.md
DATABASE.md
API.md
IMAGE_PIPELINE.md
PROVIDER_DESIGN.md
UI_UX.md
COMPLIANCE.md
MILESTONES.md
TEST_PLAN.md

然后：

检查当前仓库。

不要重复创建已有功能。

如果已有代码：

优先兼容和修改。

不要无理由重构整个项目。

==================================================
二十三、你的工作方式
==================================================

开始时先输出：

1. 当前项目状态
2. 准备实现的 Phase
3. 将修改的文件
4. 技术方案
5. 风险

然后开始编码。

每完成一个 Phase：

运行测试。

输出：

完成项
测试结果
剩余问题
下一 Phase

==================================================
二十四、最终目标
==================================================

MVP 的判断标准不是：

“代码很多”。

而是：

从登录开始，

用户能够：

创建 AI 模特
↓
上传商品
↓
创建生成任务
↓
得到图片
↓
得到文案
↓
下载素材

整个流程真实可运行。