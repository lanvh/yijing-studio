import asyncio
import io
import json
import logging
import uuid
import zipfile
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models.generation import GenerationResult, GenerationTask
from app.models.user import User
from app.providers.contracts import GenerationRequest, GenerationSettings, ImageReference
from app.providers.router import ProviderRouter
from app.schemas.generation import CopyEdit, TaskCreate
from app.services.ai_models import ModelService
from app.services.content_copy import CopyWriter
from app.services.images import ImageService
from app.services.products import ProductService
from app.services.prompts import PromptBuilder
from app.services.quality import QualityChecker
from app.storage.local import ImageStorage

logger = logging.getLogger(__name__)


class GenerationError(Exception):
    def __init__(self, message, status_code=409):
        self.message, self.status_code = message, status_code


class GenerationService:
    def __init__(self, db: Session, storage: ImageStorage, images: ImageService | None = None):
        self.db, self.storage, self.images = db, storage, images

    def owned(self, task_id, user_id, *, lock=False):
        query = (
            select(GenerationTask)
            .where(GenerationTask.id == task_id, GenerationTask.user_id == user_id)
            .options(selectinload(GenerationTask.results), selectinload(GenerationTask.copy))
        )
        if lock:
            query = query.with_for_update()
        task = self.db.scalar(query.execution_options(populate_existing=True))
        if task is None:
            raise GenerationError("任务不存在。", 404)
        return task

    def list(self, user_id, offset=0, limit=24, status=None):
        filters = [GenerationTask.user_id == user_id]
        if status:
            filters.append(GenerationTask.status == status)
        total = self.db.scalar(select(func.count()).select_from(GenerationTask).where(*filters))
        items = self.db.scalars(
            select(GenerationTask)
            .where(*filters)
            .options(selectinload(GenerationTask.results))
            .order_by(GenerationTask.created_at.desc(), GenerationTask.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()
        return dict(items=items, total=total, offset=offset, limit=limit)

    def cleanup(self, keys):
        for key in keys:
            try:
                self.storage.delete(key)
            except OSError:
                logger.error("Could not remove private task artifact")

    def create(self, user_id, payload: TaskCreate):
        self.db.scalar(select(User).where(User.id == user_id).with_for_update())
        existing = self.db.scalar(
            select(GenerationTask).where(
                GenerationTask.user_id == user_id, GenerationTask.request_key == payload.request_key
            )
        )
        values = payload.model_dump(mode="json", exclude={"request_key"})
        if existing:
            if existing.snapshot["request"] != values:
                raise GenerationError("提交标识已用于另一组参数，请重新提交。")
            self.db.commit()
            return self.owned(existing.id, user_id)
        if get_settings().image_provider != "mock":
            raise GenerationError("当前版本只支持 Mock，请将图片服务配置为 mock。", 503)
        model = ModelService(self.db, self.storage).owned(payload.model_id, user_id, lock=True)
        product = ProductService(self.db, self.storage).owned(
            payload.product_id, user_id, lock=True
        )
        if not model.reference_images or not product.processed_images:
            raise GenerationError("请先为模特和商品各上传至少一张图片。", 422)
        task_id = uuid.uuid4()
        snapshot = {
            "request": values,
            "model": {
                key: getattr(model, key)
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
                    "description",
                    "character_prompt",
                )
            },
            "product": {
                key: getattr(product, key)
                for key in ("name", "brand", "category", "color", "description", "product_features")
            },
            "character_inputs": [],
            "product_inputs": [],
        }
        written = []
        try:
            sources = [
                (
                    "character_inputs",
                    [
                        ModelService.key(user_id, model.id, image.id)
                        for image in model.reference_images[:8]
                    ],
                ),
                (
                    "product_inputs",
                    [
                        ProductService.key(user_id, product.id, image)
                        for image in product.processed_images[:8]
                    ],
                ),
            ]
            for group, keys in sources:
                for source in keys:
                    key = f"tasks/{user_id}/{task_id}/inputs/{uuid.uuid4()}.jpg"
                    self.storage.put(key, self.storage.read(source))
                    written.append(key)
                    snapshot[group].append(key)
            prompt, negative = PromptBuilder().build(snapshot)
            task = GenerationTask(
                id=task_id,
                user_id=user_id,
                provider="mock",
                snapshot=snapshot,
                prompt=prompt,
                negative_prompt=negative,
                results=[],
                **payload.model_dump(),
            )
            self.db.add(task)
            self.db.commit()
        except Exception:
            self.db.rollback()
            self.cleanup(written)
            raise
        return self.run(task_id, user_id)

    def run(self, task_id, user_id):
        task = self.owned(task_id, user_id, lock=True)
        if not task.can_retry:
            raise GenerationError("任务正在执行、已完成或已达到 3 次尝试上限。")
        task.status = "PROCESSING"
        task.attempt += 1
        attempt = task.attempt
        task.started_at = datetime.now(UTC)
        task.completed_at = None
        task.error_message = ""
        task.lease_expires_at = task.started_at + timedelta(
            seconds=get_settings().image_provider_timeout_seconds * 2 + 60
        )
        remaining = max(0, task.requested_count - len(task.results))
        snapshot, prompt, negative = task.snapshot, task.prompt, task.negative_prompt
        provider = task.provider
        self.db.commit()
        # Provider runs outside a database transaction. Attempt acts as a fencing token.
        written, outputs, jobs = [], [], []
        error = ""
        try:
            characters = tuple(
                ImageReference(data=self.storage.read(key), media_type="image/jpeg")
                for key in snapshot["character_inputs"]
            )
            products = tuple(
                ImageReference(data=self.storage.read(key), media_type="image/jpeg")
                for key in snapshot["product_inputs"]
            )
            image_service = self.images or ImageService(ProviderRouter(name=provider))
            while remaining:
                count = max(n for n in (1, 2, 4, 6) if n <= remaining)
                result = asyncio.run(
                    image_service.generate(
                        GenerationRequest(
                            prompt=prompt,
                            character_images=characters,
                            product_images=products,
                            settings=GenerationSettings(
                                requested_count=count,
                                seed=attempt * 100 + len(outputs),
                                negative_prompt=negative,
                            ),
                        )
                    )
                )
                jobs.append(result.provider_task_id)
                for image in result.images:
                    check = QualityChecker().inspect(image.data)
                    if not check["passed"]:
                        error = "图片文件检查未通过，可重试补齐。"
                        continue
                    image_id = uuid.uuid4()
                    extension = "jpg" if image.media_type == "image/jpeg" else "png"
                    key = f"tasks/{user_id}/{task_id}/outputs/{image_id}.{extension}"
                    self.storage.put(key, image.data)
                    written.append(key)
                    outputs.append(
                        GenerationResult(
                            id=image_id,
                            created_at=datetime.now(UTC),
                            task_id=task_id,
                            storage_key=key,
                            image_url=f"/api/v1/generation/results/{image_id}/image",
                            quality_score=100,
                            is_selected=True,
                            result_metadata={
                                **image.metadata,
                                "mock": provider == "mock",
                                "media_type": image.media_type,
                                "extension": extension,
                                "file_check": check,
                                "attempt": attempt,
                                "provider_task_id": result.provider_task_id,
                            },
                        )
                    )
                remaining -= count
                if not result.success:
                    error = result.error.message if result.error else "图片生成失败。"
                    break
        except Exception as exc:
            logger.error("Task generation failed: %s", type(exc).__name__)
            error = "生成或图片存储失败，请检查服务后重试。"
        try:
            task = self.owned(task_id, user_id, lock=True)
            if task.attempt != attempt or task.status != "PROCESSING":
                self.db.rollback()
                self.cleanup(written)
                return self.owned(task_id, user_id)
            task.results.extend(outputs)
            total = len(task.results)
            task.status = (
                "SUCCEEDED" if total >= task.requested_count else "PARTIAL" if total else "FAILED"
            )
            task.error_message = (
                "" if task.status == "SUCCEEDED" else error or "结果不足，请重试补齐。"
            )
            task.provider_job_id = jobs[-1] if jobs else None
            task.completed_at = datetime.now(UTC)
            task.lease_expires_at = None
            if total and task.copy is None:
                task.copy = CopyWriter().compose(task)
            self.db.commit()
        except Exception:
            self.db.rollback()
            self.cleanup(written)
            raise
        return self.owned(task_id, user_id)

    @staticmethod
    def editable(task):
        if task.is_active:
            raise GenerationError("任务正在执行，请完成后再操作。")

    def result(self, result_id, user_id, *, lock=False):
        task_id = self.db.scalar(
            select(GenerationResult.task_id)
            .join(GenerationTask)
            .where(GenerationResult.id == result_id, GenerationTask.user_id == user_id)
        )
        if task_id is None:
            raise GenerationError("图片不存在。", 404)
        task = self.owned(task_id, user_id, lock=lock)
        result = next((r for r in task.results if r.id == result_id), None)
        if result is None:
            raise GenerationError("图片不存在。", 404)
        return task, result

    def select_result(self, result_id, user_id, selected):
        task, result = self.result(result_id, user_id, lock=True)
        self.editable(task)
        result.is_selected = selected
        self.db.commit()
        return result

    def delete_result(self, result_id, user_id):
        task, result = self.result(result_id, user_id, lock=True)
        self.editable(task)
        key = result.storage_key
        task.results.remove(result)
        self.db.commit()
        self.cleanup([key])

    def delete(self, task_id, user_id):
        task = self.owned(task_id, user_id, lock=True)
        self.editable(task)
        keys = task.snapshot["character_inputs"] + task.snapshot["product_inputs"]
        keys += [r.storage_key for r in task.results]
        self.db.delete(task)
        self.db.commit()
        self.cleanup(keys)

    def write_copy(self, task_id, user_id, payload: CopyEdit | None = None):
        task = self.owned(task_id, user_id, lock=True)
        self.editable(task)
        if not task.results:
            raise GenerationError("请先生成至少一张图片。", 422)
        draft = CopyWriter().compose(task)
        if task.copy is None:
            task.copy = draft
        values = (
            payload.model_dump()
            if payload
            else {
                key: getattr(draft, key)
                for key in ("title", "caption", "hashtags", "product_summary", "styling_notes")
            }
        )
        for key, value in values.items():
            setattr(task.copy, key, value)
        task.copy.source = "user_edited" if payload else "local_template"
        self.db.commit()
        return task.copy

    def export(self, task_id, user_id):
        task = self.owned(task_id, user_id, lock=True)
        self.editable(task)
        selected = [r for r in task.results if r.is_selected]
        if not selected or task.copy is None:
            raise GenerationError("请至少选择一张图片，并保存文案后下载。", 422)
        buffer = io.BytesIO()
        manifest = {
            "task_id": str(task.id),
            "mock": task.is_mock,
            "real_generation": False,
            "requested_count": task.requested_count,
            "exported_count": len(selected),
            "status": task.status,
            "quality_scope": "file_integrity_only",
            "images": [],
        }
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for index, result in enumerate(selected, 1):
                role = "cover" if index == 1 else "image"
                name = f"{index:02d}_{role}.{result.result_metadata['extension']}"
                data = self.storage.read(result.storage_key)
                if (
                    QualityChecker().inspect(data)["sha256"]
                    != result.result_metadata["file_check"]["sha256"]
                ):
                    raise GenerationError("结果文件已损坏，请删除该图片或重新生成。", 409)
                archive.writestr(name, data)
                manifest["images"].append(
                    {
                        "file": name,
                        "id": str(result.id),
                        "file_check": result.result_metadata["file_check"],
                    }
                )
            for name, content in {
                "title.txt": task.copy.title,
                "caption.txt": task.copy.caption,
                "hashtags.txt": " ".join("#" + tag.lstrip("#") for tag in task.copy.hashtags),
                "product_summary.txt": task.copy.product_summary,
                "styling_notes.txt": task.copy.styling_notes,
                "product.json": json.dumps(task.snapshot["product"], ensure_ascii=False, indent=2),
                "manifest.json": json.dumps(manifest, ensure_ascii=False, indent=2),
                "README.txt": "Mock 演示素材，非真实 AI 换装结果。"
                "请核对图片和商品信息；由你手动发布。\n"
                "仅进行了文件完整性检查，未评估身份、商品一致性或美观度。",
            }.items():
                archive.writestr(name, content)
        self.db.commit()
        return buffer.getvalue()
