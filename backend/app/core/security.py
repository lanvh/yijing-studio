import hashlib
import secrets

from pwdlib import PasswordHash

password_hasher = PasswordHash.recommended()
# Equal password-verification work for an unknown account.
DUMMY_HASH = password_hasher.hash(secrets.token_urlsafe(32))
COOKIE_NAME = "seed_session"


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hasher.verify(password, hashed)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
