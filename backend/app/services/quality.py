import hashlib
import io

from PIL import Image


class QualityChecker:
    """File integrity only; no identity, product, anatomy or aesthetic claims."""

    def inspect(self, data: bytes) -> dict:
        valid, width, height = False, 0, 0
        try:
            with Image.open(io.BytesIO(data)) as image:
                width, height = image.size
                valid = (
                    image.format in {"JPEG", "PNG"}
                    and not getattr(image, "is_animated", False)
                    and 256 <= width <= 4096
                    and 256 <= height <= 4096
                    and len(data) <= 15 * 1024 * 1024
                )
                if valid:
                    image.load()
        except (OSError, ValueError, SyntaxError, Image.DecompressionBombError):
            valid = False
        return {
            "checker": "image_integrity_v1",
            "passed": valid,
            "width": width,
            "height": height,
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "scope": "file_integrity_only",
            "visual_quality_evaluated": False,
        }
