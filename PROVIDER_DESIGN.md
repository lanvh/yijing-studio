# Image Provider Design

所有图片厂商实现相同接口。

## Python interface

class ImageProvider:

    async def health_check(self):
        pass

    async def create_character(
        self,
        prompt,
        settings
    ):
        pass

    async def virtual_try_on(
        self,
        character_images,
        product_images,
        prompt,
        settings
    ):
        pass

    async def edit_image(
        self,
        reference_images,
        prompt,
        settings
    ):
        pass

    async def generate_scene(
        self,
        references,
        prompt,
        settings
    ):
        pass

## Provider Result

统一返回：

ProviderResult

{
  "success": true,
  "provider": "",
  "provider_task_id": "",
  "images": [],
  "metadata": {},
  "cost": null,
  "error": null
}

## Important

Provider 内部负责处理不同厂商：

认证

参数格式

上传图片

轮询

错误映射

返回图片

业务层不知道具体厂商 API 格式。

## Mock Provider

第一个必须实现。

Mock Provider 确保开发环境无 API Key 也能运行。

## Real Provider

第二阶段只选择一个。

不要同时集成 4-5 家。

先把一个跑通。

## Phase 4 当前实现

统一契约位于 backend/app/providers/contracts.py，ImageProvider 使用异步 Protocol。
已实现的五个方法为 create_character、virtual_try_on、edit_image、generate_scene、
generate_content_set；另提供 health_check。MockImageProvider 是当前唯一的实现。

调用链固定为 ImageService → ProviderRouter → ImageProvider。API 和未来业务任务服务
通过 ImageService 使用能力，不直接调用厂商接口。ProviderRouter 按 IMAGE_PROVIDER
选择实现，未知名称返回 unavailable，不静默切换成 Mock。

### 请求与图片引用

- GenerationRequest：operation、prompt、settings 和图片引用分组。
- GenerationSettings：requested_count 仅允许 1、2、4、6；width/height 为 256–1536，
  默认 768×1024；seed 为 0–4294967295；negative_prompt 为可选文本。
- 人物创建不接收参考图；试穿和内容组要求 character_images、product_images；
  编辑和场景要求 reference_images。每组最多 8 张。
- ImageReference 只承接已通过上传校验、所属用户权限校验的图片字节和 MIME；
  不接受远端 URL 或用户指定的本地路径。Phase 5 负责加载当前用户的模型与商品。
- Mock 仅记录参考图数量与内容哈希，不渲染参考图片，也不应用 negative_prompt。
  不应拿它评估人物一致性、商品还原度或图片质量。

### 返回与失败

ProviderResult 包含 success、provider、provider_task_id、images、metadata、cost、error。
provider_task_id 是 Provider 调用标识，后续业务任务自己的 ID 独立保存。
ProviderImage 的图片字节在进程内传递，JSON 序列化时排除；
提供 id、MIME、尺寸和 metadata。落盘由服务侧完成。

Mock 输出是带 MOCK / PLACEHOLDER 和 NOT AN AI-GENERATED PHOTO 标记的 JPEG。
metadata 明示 mock=true、real_generation=false、references_used=false。
相同 prompt、operation、seed 和图序号产生相同图片字节，但每次调用与图片 ID 独立。
Mock cost=0；真实 Provider 尚未实现。

success=true 表示请求张数全部成功。部分失败时 success=false、images 保留成功图片；
metadata.outcome 为 SUCCEEDED / PARTIAL / FAILED，failed_indices 指明失败位置。
error 包含 code、message、retryable。统一错误包括 invalid_input、unavailable、
timeout、generation_failed、internal_error、invalid_result。

ImageService 统一超时（默认 30 秒），检查返回 Provider 名称、张数、唯一图片 ID、
实际格式、尺寸及完整解码；无效结果不交给业务层保存。未知异常不在响应或日志中回显原始文本。
目前不自动重试，避免后续真实 Provider 重复计费；Phase 5 可按错误信息提供显式重试。
Mock 的绘图在线程中执行，调用超时不会强制终止已运行的线程；
此线程只生成有尺寸/张数上限的内存图片，不会在超时后写入文件。

### 阶段验收边界

python -m app.mock_job 在本地建立一次完整 Provider 请求，经过路由与服务得到多图结果，
保存图片与 manifest。此开发验收任务不写入 generation_tasks / generation_results。
Phase 5 再实现业务任务创建、持久化状态、结果入库与查询，Phase 6 接入创建和结果页面。


## 官方 Provider 接入版

OpenAIImageProvider 已实现统一五种操作。人物创建使用 /images/generations，
其他含参考图操作使用 /images/edits；多图按“人物在前、商品在后”上传，并在提示词中说明。
固定请求 JPEG，严格解码 Base64 并验证实际尺寸，不跟随远端 URL 下载图片。
negative_prompt 转为普通提示词约束，seed 不发送；返回 metadata 明确记录这些差异。
服务响应 usage 按原值保存，cost 未知时为 null，不声称费用为零。

OpenAIHTTP 将服务端地址限制为官方 HTTPS API；禁止重定向，限制响应体大小，
不回传原始上游错误正文，不自动重试，分别映射认证、限流、输入拒绝、超时和格式错误。
OpenAITextProvider 通过 Responses 的严格 JSON Schema 支持文案和商品图片观察；
store=false。Key 使用 SecretStr，配置状态仅返回可用性布尔值，不展示密钥。

ImageService 路由到 openai 时使用 IMAGE_API_TIMEOUT_SECONDS；Mock 继续使用原超时设置。
当前只有 Mock 与 OpenAI 两个图片实现，没有同时接入其他供应商。
官方真实网络生成尚未验收：缺少本机 API Key；离线协议与业务集成测试已覆盖。


## Seedream 更新（2026-10-01）

已接入 Seedream 5.0 Pro，当前本机不调用 OpenAI。原生 2K 竖图、多参考图、
候选并发生成、部分失败重试、参考图保存和 ZIP 来源标记已实现。
后端 222 项测试通过；真实密钥待用户本地填写。详情见 SEEDREAM_REPORT.md。
