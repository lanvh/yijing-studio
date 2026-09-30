import asyncio

from app.core.config import get_settings
from app.providers.openai_http import ExternalServiceError
from app.providers.openai_text import OpenAITextProvider
from app.services.content_copy import CopyWriter


def compose_copy(task, *, allow_fallback=True):
    draft = CopyWriter().compose(task)
    if get_settings().llm_provider in ("", "local", "mock"):
        return draft
    try:
        if get_settings().llm_provider != "openai":
            raise ExternalServiceError("当前文案服务配置不受支持。")
        facts = {
            "product": task.snapshot["product"],
            "scene": task.scene,
            "style": task.style,
            "pose": task.pose,
            "mock": task.is_mock,
        }
        # Only confirmed user-provided fields are used as copywriting evidence.
        facts["product"] = {k: v for k, v in facts["product"].items() if k != "product_features"}
        facts["confirmed_features"] = (
            task.snapshot["product"].get("product_features", {}).get("confirmed", {})
        )
        output = asyncio.run(OpenAITextProvider().copy(facts))
        text = output.title + output.caption
        if any(
            phrase in text
            for phrase in ("我穿了", "实测", "官方正品", "100%有效", "绝对舒服", "全网最低")
        ):
            raise ExternalServiceError(
                "文案包含未经证实的体验或承诺，请重新生成。", "invalid_result"
            )
        for key, value in output.model_dump().items():
            setattr(draft, key, value)
        marker = "【Mock 流程演示，非真实试穿】" if task.is_mock else "【AI 辅助视觉展示】"
        draft.caption = marker + "\n" + draft.caption[:4950]
        draft.source = "openai"
        return draft
    except ExternalServiceError:
        if not allow_fallback:
            raise
        draft.source = "local_fallback"
        return draft
