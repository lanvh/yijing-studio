import hashlib
import io
import warnings
from dataclasses import dataclass
from pathlib import PurePosixPath

from fastapi import UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import get_settings


class UploadRejected(Exception):
    def __init__(self, message: str, status_code: int = 422):
        self.message = message
        self.status_code = status_code


@dataclass
class ValidatedImage:
    data: bytes
    metadata: dict


def validate_reference(upload: UploadFile) -> ValidatedImage:
    settings = get_settings()
    max_bytes = settings.max_image_size_mb * 1024 * 1024
    extension = PurePosixPath((upload.filename or "").replace("\\", "/")).suffix.lower()
    formats = {
        ".jpg": ("JPEG", "image/jpeg"),
        ".jpeg": ("JPEG", "image/jpeg"),
        ".png": ("PNG", "image/png"),
        ".webp": ("WEBP", "image/webp"),
    }
    if extension not in formats:
        raise UploadRejected("仅支持 JPG、PNG 或 WebP 图片。", 415)
    expected_format, expected_mime = formats[extension]
    allowed = {value.strip() for value in settings.allowed_image_types.split(",")}
    if upload.content_type != expected_mime or expected_mime not in allowed:
        raise UploadRejected("图片扩展名与 MIME 类型不匹配。", 415)
    if upload.size is not None and upload.size > max_bytes:
        raise UploadRejected(f"单张图片不能超过 {settings.max_image_size_mb} MB。", 413)
    raw = upload.file.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise UploadRejected(f"单张图片不能超过 {settings.max_image_size_mb} MB。", 413)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as image:
                if image.format != expected_format:
                    raise UploadRejected("图片实际格式与扩展名不匹配。", 415)
                if image.width * image.height > settings.max_image_pixels:
                    raise UploadRejected("图片像素数过大，请缩小后重试。")
                if max(image.size) > 8192 or min(image.size) < 32:
                    raise UploadRejected("图片每边须为 32–8192 像素。")
                if getattr(image, "n_frames", 1) != 1:
                    raise UploadRejected("请上传静态图片。")
                image.verify()
            with Image.open(io.BytesIO(raw)) as image:
                image.load()
                oriented = ImageOps.exif_transpose(image).convert("RGBA")
                clean = Image.new("RGB", oriented.size, "white")
                clean.paste(oriented, mask=oriented.getchannel("A"))
                output = io.BytesIO()
                clean.save(output, format="JPEG", quality=95)
                data = output.getvalue()
                width, height = clean.size
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        SyntaxError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise UploadRejected("无法读取完整图片，请换一张有效图片。") from exc
    if len(data) > max_bytes:
        raise UploadRejected("处理后的图片过大，请缩小后重试。", 413)
    return ValidatedImage(
        data,
        {
            "width": width,
            "height": height,
            "size_bytes": len(data),
            "mime_type": "image/jpeg",
            "sha256": hashlib.sha256(data).hexdigest(),
            "original_sha256": hashlib.sha256(raw).hexdigest(),
            "original_mime_type": expected_mime,
        },
    )
