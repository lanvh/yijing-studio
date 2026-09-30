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