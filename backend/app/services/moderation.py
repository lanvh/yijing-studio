from datetime import UTC, datetime

from app.services.image_uploads import UploadRejected


class ReferenceUploadPolicy:
    """Phase 2 declaration checks; automated visual moderation is not integrated."""

    def review(self, rights_confirmed: bool) -> dict:
        if not rights_confirmed:
            raise UploadRejected("请确认图片为有使用权的 AI 虚拟成人形象，非真人照片。")
        return {
            "source_type": "ai_virtual",
            "rights_confirmed": True,
            "adult_virtual_confirmed": True,
            "confirmed_at": datetime.now(UTC).isoformat(),
            "moderation_status": "not_screened",
        }
