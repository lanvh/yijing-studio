import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.product import Product


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def owned(self, product_id: uuid.UUID, user_id: uuid.UUID, *, lock=False) -> Product | None:
        statement = (
            select(Product)
            .where(Product.id == product_id, Product.user_id == user_id)
            .options(selectinload(Product.images))
        )
        if lock:
            statement = statement.with_for_update()
        return self.db.scalar(statement)

    def list(self, user_id: uuid.UUID, query: str, category: str | None, offset: int, limit: int):
        filters = [Product.user_id == user_id]
        if query:
            filters.append(
                or_(
                    Product.name.contains(query, autoescape=True),
                    Product.brand.contains(query, autoescape=True),
                )
            )
        if category:
            filters.append(Product.category == category)
        total = self.db.scalar(select(func.count()).select_from(Product).where(*filters))
        products = self.db.scalars(
            select(Product)
            .where(*filters)
            .options(selectinload(Product.images))
            .order_by(Product.created_at.desc(), Product.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()
        return {"items": products, "total": total, "limit": limit, "offset": offset}
