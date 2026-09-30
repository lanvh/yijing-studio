import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.ai_model import AIModel


class ModelRepository:
    def __init__(self, db: Session):
        self.db = db

    def owned(self, model_id: uuid.UUID, user_id: uuid.UUID, *, lock=False) -> AIModel | None:
        statement = (
            select(AIModel)
            .where(AIModel.id == model_id, AIModel.user_id == user_id)
            .options(selectinload(AIModel.reference_images))
        )
        if lock:
            statement = statement.with_for_update()
        return self.db.scalar(statement)

    def list(self, user_id: uuid.UUID, query: str, offset: int, limit: int):
        filters = [AIModel.user_id == user_id]
        if query:
            filters.append(AIModel.name.contains(query, autoescape=True))
        total = self.db.scalar(select(func.count()).select_from(AIModel).where(*filters))
        models = self.db.scalars(
            select(AIModel)
            .where(*filters)
            .options(selectinload(AIModel.reference_images))
            .order_by(AIModel.created_at.desc(), AIModel.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()
        return {"items": models, "total": total, "offset": offset, "limit": limit}
