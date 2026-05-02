import random
from datetime import timedelta
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.core.errors import (
    AccountDisabledError,
    AccountUnverifiedError,
    EmailExistsError,
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


async def ensure_default_roles(session: AsyncSession) -> None:
    result = await session.execute(select(Role.name))
    existing = set(result.scalars().all())
    for name, description in DEFAULT_ROLES.items():
        if name not in existing:
            session.add(Role(name=name, description=description))
    await session.flush()


async def get_roles_for_user(session: AsyncSession, user_id: UUID) -> list[str]:
    result = await session.execute(
        select(Role.name)
        .select_from(user_roles.join(Role, user_roles.c.role_id == Role.id))
        .where(user_roles.c.user_id == user_id)
        .order_by(Role.name)
    )
    return list(result.scalars().all())


def _otp_code() -> str:
    return f"{random.randint(0, 999999):06d}"


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
