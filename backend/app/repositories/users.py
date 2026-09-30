from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.user import AuthSession, User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email.lower()))

    def create(self, *, email: str, password_hash: str, display_name: str, role: str) -> User:
        user = User(
            email=email.lower(),
            password_hash=password_hash,
            display_name=display_name,
            role=role,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def user_for_session(self, token_hash: str) -> User | None:
        return self.db.scalar(
            select(User)
            .join(AuthSession, AuthSession.user_id == User.id)
            .where(
                AuthSession.token_hash == token_hash,
                AuthSession.expires_at > datetime.now(UTC),
                User.enabled.is_(True),
            )
        )

    def delete_session(self, token_hash: str) -> None:
        self.db.execute(delete(AuthSession).where(AuthSession.token_hash == token_hash))

    def delete_expired_sessions(self) -> None:
        self.db.execute(delete(AuthSession).where(AuthSession.expires_at <= datetime.now(UTC)))
