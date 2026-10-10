import base64
import hashlib
import io
import ipaddress
import secrets
import time
from urllib.parse import urlsplit

import qrcode
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.generation import GenerationTask
from app.services.generation import GenerationError, GenerationService


def public_base():
    base = get_settings().mobile_public_url.rstrip("/")
    url = urlsplit(base)
    try:
        valid = url.scheme == "https" or (
            url.scheme == "http"
            and ipaddress.ip_address(url.hostname).is_private
            and not ipaddress.ip_address(url.hostname).is_loopback
        )
    except ValueError:
        valid = False
    if (
        not valid
        or not url.hostname
        or url.username
        or url.password
        or url.query
        or url.fragment
        or url.path
    ):
        raise GenerationError("手机访问地址未配置，请通过 start-local.ps1 重新启动项目。", 503)
    return base


class MobileTransfer:
    def __init__(self, db, storage):
        self.db, self.storage = db, storage

    def create(self, task_id, user_id):
        base = public_base()
        task = GenerationService(self.db, self.storage).owned(task_id, user_id, lock=True)
        GenerationService.editable(task)
        selected = [str(r.id) for r in task.results if r.is_selected]
        if not selected or not task.copy:
            raise GenerationError("请先选择至少一张图片并保存文案。", 422)
        token = secrets.token_urlsafe(32)
        expires = int(time.time()) + 3600
        task.snapshot = {
            **task.snapshot,
            "mobile_transfer": {
                "token_hash": hashlib.sha256(token.encode()).hexdigest(),
                "expires_at": expires,
                "image_ids": selected,
                "title": task.copy.title,
                "caption": task.copy.caption,
                "hashtags": task.copy.hashtags,
            },
        }
        self.db.commit()
        link = f"{base}/mobile-publish/{task.id}#{token}"
        buffer = io.BytesIO()
        qrcode.make(link).save(buffer, format="PNG")
        return {
            "url": link,
            "expires_at": expires,
            "qr_image": "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode(),
        }

    def revoke(self, task_id, user_id):
        task = GenerationService(self.db, self.storage).owned(task_id, user_id, lock=True)
        snapshot = dict(task.snapshot)
        snapshot.pop("mobile_transfer", None)
        task.snapshot = snapshot
        self.db.commit()

    def read(self, task_id, token):
        task = self.db.scalar(
            select(GenerationTask)
            .where(GenerationTask.id == task_id)
            .options(selectinload(GenerationTask.results))
        )
        share = task.snapshot.get("mobile_transfer", {}) if task else {}
        supplied = hashlib.sha256((token or "").encode()).hexdigest()
        if (
            not token
            or len(token) > 100
            or not share
            or not secrets.compare_digest(share.get("token_hash", ""), supplied)
            or share.get("expires_at", 0) <= time.time()
        ):
            raise GenerationError("取图链接已失效，请在电脑上重新生成二维码。", 404)
        results = [r for r in task.results if str(r.id) in share["image_ids"] and r.is_selected]
        return share, results

    def content(self, task_id, token):
        share, results = self.read(task_id, token)
        return {
            "title": share["title"],
            "caption": share["caption"],
            "hashtags": share["hashtags"],
            "expires_at": share["expires_at"],
            "images": [
                {"id": str(r.id), "name": f"穿搭图片 {i + 1}"} for i, r in enumerate(results)
            ],
        }

    def image(self, task_id, image_id, token):
        _, results = self.read(task_id, token)
        result = next((r for r in results if r.id == image_id), None)
        if result is None:
            raise GenerationError("图片不存在或已取消选择。", 404)
        return self.storage.read(result.storage_key), result.result_metadata.get(
            "media_type", "image/jpeg"
        )
