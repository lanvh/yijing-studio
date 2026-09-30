import json


class PromptBuilder:
    """Compose internal prompts from owned, snapshotted facts. Mock does not render them."""

    negative = (
        "extra fingers, deformed hands, duplicated shoes, incorrect logo, "
        "changed product color, distorted clothing, unreal anatomy"
    )

    def build(self, snapshot: dict) -> tuple[str, str]:
        request = snapshot["request"]
        model, product = snapshot["model"], snapshot["product"]
        facts = {
            "character": {
                key: str(model.get(key, ""))[:200]
                for key in (
                    "name",
                    "gender",
                    "age_range",
                    "height",
                    "body_type",
                    "skin_tone",
                    "hair_style",
                    "hair_color",
                    "style",
                )
            },
            "product": {
                key: str(product.get(key, ""))[:200]
                for key in ("name", "brand", "category", "color")
            },
            "confirmed_features": product.get("product_features", {}).get("confirmed", {}),
        }
        instructions = (
            "Preserve character identity. Preserve product color, structure and original logos. "
            "Natural hands and feet, realistic photography, coherent lighting and shadows. "
            "Do not invent product features. "
            f"Scene: {request['scene']}. Style: {request['style']}. Pose: {request['pose']}. "
        )
        return instructions + "Supplied facts: " + json.dumps(
            facts, ensure_ascii=False, sort_keys=True
        )[:5200], self.negative
