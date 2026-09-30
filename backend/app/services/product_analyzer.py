import io
from datetime import UTC, datetime

from PIL import Image

from app.models.product import Product
from app.schemas.product import ProductFeatureNotes


def image_palette(data: bytes) -> list[str]:
    """Whole-image pixel statistics; this does not identify or segment a product."""
    with Image.open(io.BytesIO(data)) as image:
        small = image.convert("RGB").resize((64, 64))
        quantized = small.quantize(colors=4)
        palette = quantized.getpalette()
        colors = sorted(quantized.getcolors() or [], reverse=True)
        return [
            "#{:02x}{:02x}{:02x}".format(*palette[index * 3 : index * 3 + 3]) for _, index in colors
        ]


class ProductAnalyzer:
    """Collect attributable facts without fabricating visual or material recognition."""

    def analyze(self, product: Product, notes: dict | None = None) -> dict:
        confirmed = ProductFeatureNotes.model_validate(
            notes if notes is not None else (product.product_features or {}).get("confirmed", {})
        ).model_dump()
        images = product.processed_images
        return {
            "schema_version": 1,
            "analyzer": "local_evidence_v1",
            "status": "user_data_and_image_statistics" if images else "user_data_only",
            "category": product.category,
            "brand": product.brand or None,
            "color": [product.color] if product.color else [],
            "description": product.description,
            "material": confirmed["material"] or None,
            "material_guess": None,
            "pattern": confirmed["pattern"] or None,
            "logo_description": confirmed["logo_description"] or None,
            "shape": confirmed["shape"] or None,
            "critical_features": confirmed["critical_features"],
            "confirmed": confirmed,
            "sources": {
                "product_fields": "user_provided",
                "confirmed": "user_provided",
                "image_observations": "pixel_statistics",
            },
            "image_observations": [
                {
                    "image_id": str(image.id),
                    "width": image.image_metadata["width"],
                    "height": image.image_metadata["height"],
                    "palette": image.image_metadata["palette"],
                }
                for image in images
            ],
            "limitations": [
                "图片色板包含背景，不代表商品主色。",
                "未执行材质、品牌、Logo、图案或结构的视觉识别；未知信息保持为空。",
            ],
            "analyzed_at": datetime.now(UTC).isoformat(),
        }
