from app.models.generation import ContentCopy, GenerationTask
from app.schemas.generation import SCENES, STYLES


class CopyWriter:
    """Readable local fallback using only named/confirmed facts."""

    def compose(self, task: GenerationTask) -> ContentCopy:
        product = task.snapshot["product"]
        name = product["name"]
        style = STYLES.get(task.style, task.style)
        scene = SCENES.get(task.scene, task.scene)
        confirmed = product.get("product_features", {}).get("confirmed", {})
        facts = []
        for key, label in [("brand", "品牌"), ("color", "颜色")]:
            if product.get(key):
                facts.append(f"{label}：{product[key]}")
        for key, label in [("material", "材质"), ("pattern", "图案"), ("shape", "结构")]:
            if confirmed.get(key):
                facts.append(f"{label}：{confirmed[key]}")
        summary = "；".join(facts) or "外观参考上传图片，具体信息以实物为准。"
        detail = "，".join(facts) if facts else "把这件单品作为搭配主角，围绕它安排整体造型"
        marker = "【Mock 流程演示，非真实试穿】" if task.is_mock else "【AI 辅助视觉展示】"
        return ContentCopy(
            task_id=task.id,
            title=f"{name}✨{style}搭配的氛围感"[:200],
            caption=f"{marker}\n\n{detail}。\n\n"
            f"这组搭配围绕{style}展开，让主单品与整体造型形成呼应。\n\n"
            f"把拍摄安排在{scene}，留下一组日常穿搭灵感📷",
            hashtags=[name[:50], style, scene, "日常穿搭", "穿搭灵感"],
            product_summary=summary[:2000],
            styling_notes=f"{style}风格，{scene}场景；保持商品外观，具体搭配以图片与实物为准。",
            source="local_template",
        )
