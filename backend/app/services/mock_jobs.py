import json
import logging
import uuid
from datetime import UTC, datetime

from app.providers.contracts import GenerationRequest
from app.services.images import ImageService
from app.storage.local import ImageStorage

logger = logging.getLogger(__name__)


class MockJobRunner:
    """Development harness. No business task records, public files or DB connections."""

    def __init__(self, service: ImageService, storage: ImageStorage):
        self.service = service
        self.storage = storage

    async def run(self, request: GenerationRequest) -> tuple[str, dict]:
        if self.service.router.name != "mock":
            raise ValueError("The development runner only accepts the mock provider.")
        result = await self.service.generate(request)
        job_id = uuid.uuid4()
        prefix = f"mock_jobs/{job_id}"
        manifest_key = f"{prefix}/manifest.json"
        manifest = {
            "schema_version": 1,
            "development_only": True,
            "created_at": datetime.now(UTC).isoformat(),
            "request": {
                "operation": request.operation,
                "settings": request.settings.model_dump(mode="json"),
            },
            "result": result.model_dump(mode="json"),
        }
        written = []
        try:
            for image, descriptor in zip(result.images, manifest["result"]["images"], strict=True):
                extension = "jpg" if image.media_type == "image/jpeg" else "png"
                key = f"{prefix}/{image.id}.{extension}"
                self.storage.put(key, image.data)
                written.append(key)
                descriptor["storage_key"] = key
            self.storage.put(
                manifest_key, json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
            )
            written.append(manifest_key)
        except Exception:
            for key in written:
                try:
                    self.storage.delete(key)
                except OSError:
                    logger.error("Could not clean up mock job file: %s", key)
            raise
        return manifest_key, manifest
