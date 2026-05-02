"""
Backend documentation for `core/security.py`.

This core utility module centralizes shared backend behavior such as security, dependency injection, errors, or time handling.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from datetime import timedelta
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from SRC.Backend.config import get_settings
from SRC.Backend.core.time import utcnow

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# Function explanation:
# `hash_password` centralizes password hashing using `passlib`'s
# `CryptContext` with bcrypt. Centralization ensures consistent hashing
# parameters and simplifies upgrades (e.g., changing to Argon2) in one place.
#
# Alternative (commented): use Argon2 for stronger hashing if available.
#
# from passlib.hash import argon2
# def hash_password_argon2(password: str) -> str:
#     return argon2.hash(password)


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


# Function explanation:
# `verify_password` checks a plaintext password against a stored hash using
# the same `CryptContext`. It returns True when they match.
#
# Alternative (commented): use constant-time comparison with a dedicated
# verifier or perform rehashing if the stored hash uses deprecated params.
#
# def verify_and_upgrade(password: str, password_hash: str) -> tuple[bool, str|None]:
#     ok = pwd_context.verify(password, password_hash)
#     new_hash = None
#     if ok and pwd_context.needs_update(password_hash):
#         new_hash = pwd_context.hash(password)
#     return ok, new_hash


# Backend note: Creates a new domain record after validation and keeps side effects scoped to this workflow.
def create_access_token(user_id: UUID, roles: list[str]) -> str:
    settings = get_settings()
    expires = utcnow() + timedelta(seconds=settings.jwt_access_ttl_seconds)
    payload = {"sub": str(user_id), "roles": roles, "exp": expires}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


# Function explanation:
# `create_access_token` builds a JWT containing the user id and roles,
# with expiration. It uses `python-jose` for encoding and respects TTL from
# settings. Storing roles in the token enables stateless role checks.
#
# Alternative (commented): use opaque tokens stored in DB for immediate
# revocation (store token id in DB and return that instead of JWT).
#
# import secrets
# def create_opaque_access_token(user_id: UUID, roles: list[str]) -> str:
#     token = secrets.token_urlsafe(32)
#     # Persist token with user_id, roles, expiry in a DB table
#     return token


# Backend note: Creates a new domain record after validation and keeps side effects scoped to this workflow.
def create_reset_token(user_id: UUID) -> str:
    settings = get_settings()
    expires = utcnow() + timedelta(seconds=settings.reset_token_ttl_seconds)
    payload = {"sub": str(user_id), "purpose": "password_reset", "exp": expires}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


# Function explanation:
# `create_reset_token` issues a short-lived JWT specifically for password
# reset flows by including a `purpose` claim. This separates reset tokens
# from access tokens and allows targeted validation.
#
# Alternative (commented): generate a one-time random token and persist a
# hash of it in a `password_resets` table to allow revocation and single-use.
#
# import secrets, hashlib
# def create_db_backed_reset_token(user_id: UUID) -> str:
#     token = secrets.token_urlsafe(32)
#     token_hash = hashlib.sha256(token.encode()).hexdigest()
#     # persist token_hash with user_id and expiry
#     return token


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
def decode_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("invalid_token") from exc


# Function explanation:
# `decode_token` verifies and decodes a JWT, raising a `ValueError` on
# failure. Centralizing decode logic ensures consistent error handling.
#
# Alternative (commented): return `None` on invalid tokens or raise more
# specific application exceptions to map to HTTP responses in the route layer.
#
# def decode_token_safe(token: str) -> dict|None:
#     try:
#         return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
#     except JWTError:
#         return None
