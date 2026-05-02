"""
Backend documentation for `services/auth_service.py`.

This service module owns business rules and database coordination so route handlers and UI code stay simple.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

import random
import secrets
from datetime import timedelta
from uuid import UUID

import httpx
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.core.errors import (
    AccountDisabledError,
    AccountUnverifiedError,
    EmailExistsError,
    GoogleAuthError,
    GoogleNotConfiguredError,
    InvalidCredentialsError,
    NotFoundError,
    OtpExpiredError,
)
from SRC.Backend.core.security import create_access_token, create_reset_token, decode_token, hash_password, verify_password
from SRC.Backend.core.time import utcnow
from SRC.Backend.db.models import OtpVerification, Role, User, user_roles
from SRC.Backend.services.notification_service import queue_email

DEFAULT_ROLES = {
    "customer": "Books appointments and manages own bookings",
    "organiser": "Creates appointment types and manages bookings",
    "admin": "Manages users, roles, and global system state",
}


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
async def ensure_default_roles(session: AsyncSession) -> None:
    result = await session.execute(select(Role.name))
    existing = set(result.scalars().all())
    for name, description in DEFAULT_ROLES.items():
        if name not in existing:
            session.add(Role(name=name, description=description))
    await session.flush()


    # Explanation:
    # `ensure_default_roles` ensures that the application's default role
    # records exist. It queries existing names and inserts missing ones.
    #
    # Alternative (commented, placed immediately below function):
    # Use an idempotent `upsert` (ON CONFLICT) to avoid race conditions in
    # high-concurrency environments.
    #
    # async def ensure_default_roles_upsert(session: AsyncSession) -> None:
    #     for name, description in DEFAULT_ROLES.items():
    #         await session.execute(text("""
    #             INSERT INTO roles (name, description) VALUES (:name, :description)
    #             ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description
    #         """), {"name": name, "description": description})


# Backend note: Reads data and shapes it for the caller without mutating booking state unless noted by the implementation.
async def get_roles_for_user(session: AsyncSession, user_id: UUID) -> list[str]:
    result = await session.execute(
        select(Role.name)
        .select_from(user_roles.join(Role, user_roles.c.role_id == Role.id))
        .where(user_roles.c.user_id == user_id)
        .order_by(Role.name)
    )
    return list(result.scalars().all())


    # Explanation:
    # `get_roles_for_user` returns role names ordered for a given user id by
    # querying the association table. This keeps role resolution efficient.
    #
    # Alternative (commented): cache role lookups in Redis for hot users to
    # reduce DB joins on frequently accessed accounts.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
def _otp_code() -> str:
    return f"{random.randint(0, 999999):06d}"


# Explanation:
# `_otp_code` generates a zero-padded 6-digit OTP string.
#
# Alternative (commented): use an HMAC-based OTP (TOTP/HOTP) for better
# security and server-side validation without persistent storage.
#
# def _otp_totp(secret: str) -> str:
#     import pyotp
#     return pyotp.TOTP(secret).now()


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
async def signup(session: AsyncSession, payload, otp_ttl_seconds: int) -> tuple[User, str]:
    async with session.begin():
        await ensure_default_roles(session)
        existing = await session.scalar(select(User).where(User.email == payload.email.lower()))
        if existing:
            raise EmailExistsError()

        user = User(
            full_name=payload.full_name,
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            timezone=payload.timezone,
        )
        session.add(user)
        await session.flush()

        role = await session.scalar(select(Role).where(Role.name == "customer"))
        await session.execute(insert(user_roles).values(user_id=user.id, role_id=role.id))

        code = _otp_code()
        session.add(
            OtpVerification(
                user_id=user.id,
                otp_code=code,
                otp_type="email_verify",
                expires_at=utcnow() + timedelta(seconds=otp_ttl_seconds),
            )
        )
        queue_email(
            session,
            event_type="email_verify",
            recipient_id=user.id,
            subject="Your verification code",
            body=f"Your OverClocked verification code is {code}.",
        )
    return user, code


    # Explanation:
    # `signup` creates a new `User` row, assigns the `customer` role, and
    # emits an OTP verification record and email. It runs inside a DB
    # transaction to ensure atomicity.
    #
    # Alternative (commented): separate user creation and OTP issuance into
    # two steps so the account can be created first and email sending can be
    # retried independently.
    #
    # async def signup_create_user_then_otp(session, payload, otp_ttl_seconds):
    #     user = User(...)
    #     session.add(user)
    #     await session.flush()
    #     # commit here or return user and handle OTP outside transaction
    #     return user


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
async def verify_otp(session: AsyncSession, email: str, otp: str) -> bool:
    async with session.begin():
        user = await session.scalar(select(User).where(User.email == email.lower()))
        if not user:
            raise NotFoundError("user")
        record = await session.scalar(
            select(OtpVerification)
            .where(
                OtpVerification.user_id == user.id,
                OtpVerification.otp_code == otp,
                OtpVerification.otp_type == "email_verify",
                OtpVerification.is_used.is_(False),
            )
            .order_by(OtpVerification.created_at.desc())
        )
        if not record or record.expires_at < utcnow():
            raise OtpExpiredError()
        record.is_used = True
        user.is_verified = True
    return True


    # Explanation:
    # `verify_otp` finds the most recent unused OTP for the user, validates
    # expiry, marks it used, and flips `user.is_verified`. It raises specific
    # errors for missing records or expiry.
    #
    # Alternative (commented): validate OTPs against a one-time token table
    # storing hashed OTPs to avoid storing plaintext codes in DB.
    #
    # async def verify_otp_hashed(session, email, otp):
    #     otp_hash = hashlib.sha256(otp.encode()).hexdigest()
    #     # lookup by hash and validate
    #     pass


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
async def resend_otp(session: AsyncSession, email: str, otp_ttl_seconds: int) -> str:
    async with session.begin():
        user = await session.scalar(select(User).where(User.email == email.lower()))
        if not user:
            raise NotFoundError("user")
        code = _otp_code()
        session.add(
            OtpVerification(
                user_id=user.id,
                otp_code=code,
                otp_type="email_verify",
                expires_at=utcnow() + timedelta(seconds=otp_ttl_seconds),
            )
        )
        queue_email(
            session,
            event_type="email_verify",
            recipient_id=user.id,
            subject="Your verification code",
            body=f"Your OverClocked verification code is {code}.",
        )
    return code


    # Explanation:
    # `resend_otp` issues a fresh OTP and queues an email. Rate limiting and
    # abuse prevention should be enforced at the service or API layer.
    #
    # Alternative (commented): reuse the last unexpired OTP instead of
    # issuing a new one when within a short window to avoid spamming users.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
async def login(session: AsyncSession, email: str, password: str) -> tuple[str, User, list[str]]:
    user = await session.scalar(select(User).where(User.email == email.lower()))
    if not user or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()
    if not user.is_active:
        raise AccountDisabledError()
    if not user.is_verified:
        raise AccountUnverifiedError()
    roles = await get_roles_for_user(session, user.id)
    token = create_access_token(user.id, roles)
    return token, user, roles


    # Explanation:
    # `login` authenticates the user, enforces active/verified flags, fetches
    # roles, and returns a JWT access token. Error types are raised for
    # specific failure cases to map to HTTP responses.
    #
    # Alternative (commented): implement account lockout on repeated failed
    # logins using a counter in DB or cache to mitigate brute-force attacks.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
async def forgot_password(session: AsyncSession, email: str) -> None:
    async with session.begin():
        user = await session.scalar(select(User).where(User.email == email.lower()))
        if not user:
            return
        token = create_reset_token(user.id)
        queue_email(
            session,
            event_type="password_reset",
            recipient_id=user.id,
            subject="Reset your password",
            body=f"Use this reset token: {token}",
        )


    # Explanation:
    # `forgot_password` emits a reset token via email if the user exists.
    # It intentionally does not reveal account existence to callers.
    #
    # Alternative (commented): store reset tokens in a `password_resets` table
    # with hashed tokens for single-use and revocation.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
async def google_login(session: AsyncSession, id_token: str, google_client_id: str) -> tuple[str, "User", list[str]]:
    if not google_client_id:
        raise GoogleNotConfiguredError()

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            "https://www.googleapis.com/oauth2/v3/tokeninfo",
            params={"id_token": id_token},
        )

    if response.status_code != 200:
        raise GoogleAuthError()

    data = response.json()

    aud = data.get("aud", "")
    valid_aud = google_client_id in aud if isinstance(aud, list) else aud == google_client_id
    if not valid_aud:
        raise GoogleAuthError()

    if not data.get("email_verified"):
        raise GoogleAuthError()

    email = data.get("email", "").lower()
    if not email:
        raise GoogleAuthError()

    full_name = data.get("name") or email.split("@")[0]

    async with session.begin():
        await ensure_default_roles(session)
        user = await session.scalar(select(User).where(User.email == email))

        if not user:
            user = User(
                full_name=full_name,
                email=email,
                password_hash=hash_password(secrets.token_urlsafe(32)),
                timezone="UTC",
                is_verified=True,
            )
            session.add(user)
            await session.flush()
            role = await session.scalar(select(Role).where(Role.name == "customer"))
            await session.execute(insert(user_roles).values(user_id=user.id, role_id=role.id))
        elif not user.is_active:
            raise AccountDisabledError()
        elif not user.is_verified:
            user.is_verified = True

    roles = await get_roles_for_user(session, user.id)
    token = create_access_token(user.id, roles)
    return token, user, roles


async def reset_password(session: AsyncSession, token: str, new_password: str) -> bool:
    try:
        payload = decode_token(token)
        if payload.get("purpose") != "password_reset":
            raise ValueError("wrong_purpose")
        user_id = UUID(payload["sub"])
    except Exception as exc:
        raise OtpExpiredError() from exc

    async with session.begin():
        user = await session.get(User, user_id)
        if not user:
            raise NotFoundError("user")
        user.password_hash = hash_password(new_password)
    return True


    # Explanation:
    # `reset_password` decodes a JWT reset token, validates purpose, and
    # updates the user's hashed password inside a DB transaction.
    #
    # Alternative (commented): use DB-backed single-use reset tokens and
    # delete/mark-used after consumption for stronger revocation semantics.
