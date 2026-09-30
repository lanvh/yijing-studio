import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import DUMMY_HASH, hash_password, hash_token, verify_password
from app.models.user import AuthSession, User
from app.repositories.users import UserRepository


class InvalidCredentials(Exception):
    pass


class DuplicateUser(Exception):
    pass


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def create_user(self, email: str, password: str, display_name: str, role: str) -> User:
        if not 12 <= len(password) <= 128:
            raise ValueError("Password must contain 12 to 128 characters.")
        if not display_name.strip() or len(display_name) > 100:
            raise ValueError("Display name must contain 1 to 100 characters.")
        if role not in {"admin", "user"}:
            raise ValueError("Invalid role.")
        if self.users.by_email(email):
            raise DuplicateUser
        try:
            user = self.users.create(
                email=email,
                password_hash=hash_password(password),
                display_name=display_name.strip(),
                role=role,
            )
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateUser from exc
        return user

    def login(
        self, email: str, password: str, previous_token: str | None = None
    ) -> tuple[User, str]:
        user = self.users.by_email(email)
        valid = verify_password(password, user.password_hash if user else DUMMY_HASH)
        if not user or not valid or not user.enabled:
            raise InvalidCredentials
        token = secrets.token_urlsafe(32)
        self.users.delete_expired_sessions()
        if previous_token:
            self.users.delete_session(hash_token(previous_token))
        self.db.add(
            AuthSession(
                token_hash=hash_token(token),
                user_id=user.id,
                expires_at=datetime.now(UTC)
                + timedelta(minutes=get_settings().session_expire_minutes),
            )
        )
        self.db.commit()
        return user, token

    def current_user(self, token: str | None) -> User | None:
        if not token or len(token) > 256:
            return None
        return self.users.user_for_session(hash_token(token))

    def logout(self, token: str | None) -> None:
        if token and len(token) <= 256:
            self.users.delete_session(hash_token(token))
            self.db.commit()
