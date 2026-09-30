from app.models.generation import ContentCopy, GenerationTask
from app.schemas.generation import SCENES, STYLES


class CopyWriter:
    """Deterministic drafts derived only from supplied product facts, no invented experience."""

    def compose(self, task: GenerationTask) -> ContentCopy:
        product = task.snapshot["product"]
        name = product["name"]
        facts = []
        for key, label in [("brand", "品牌"), ("color", "颜色")]:
            if product.get(key):
                facts.append(f"{label}：{product[key]}")
        confirmed = product.get("product_features", {}).get("confirmed", {})
        for key, label in [("material", "材质"), ("pattern", "图案"), ("shape", "结构")]:
            if confirmed.get(key):
                facts.append(f"{label}：{confirmed[key]}")
        summary = "；".join(facts) or "商品细节待补充，以实物和已确认资料为准。"
        marker = "【Mock 流程演示，非真实试穿】" if task.is_mock else "【AI 辅助视觉展示】"
        return ContentCopy(
            task_id=task.id,
            title=f"{name}｜{STYLES[task.style]}搭配灵感"[:200],
            caption=f"{marker}\n围绕「{name}」整理一组{SCENES[task.scene]}场景的搭配参考。\n"
            f"已提供的商品信息：{summary}\n"
            "图片仅作视觉创意参考，不代表真实试穿或使用体验；发布前请核对商品信息。",
            hashtags=["搭配灵感", STYLES[task.style], SCENES[task.scene]],
            product_summary=summary[:2000],
            styling_notes=f"建议围绕{STYLES[task.style]}风格与{SCENES[task.scene]}场景安排构图，"
            "保留商品原有颜色、结构与 Logo；具体搭配请人工确认。",
            source="local_template",
        )
