from datetime import timedelta
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from SRC.Backend.config import get_settings
from SRC.Backend.core.time import utcnow

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(user_id: UUID, roles: list[str]) -> str:
    settings = get_settings()
    expires = utcnow() + timedelta(seconds=settings.jwt_access_ttl_seconds)
    payload = {"sub": str(user_id), "roles": roles, "exp": expires}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_reset_token(user_id: UUID) -> str:
    settings = get_settings()
    expires = utcnow() + timedelta(seconds=settings.reset_token_ttl_seconds)
    payload = {"sub": str(user_id), "purpose": "password_reset", "exp": expires}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("invalid_token") from exc
