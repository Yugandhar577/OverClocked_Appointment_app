"""
Backend documentation for `db/models/auth.py`.

This model module declares database persistence structures and relationships used by SQLAlchemy.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from SRC.Backend.db.base import Base


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("granted_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("granted_by", UUID(as_uuid=True), ForeignKey("users.id"), nullable=True),
)


# Backend note: Groups related backend data or behavior for a single domain concept.
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    timezone: Mapped[str] = mapped_column(String(60), default="UTC", nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    profile_photo: Mapped[str | None] = mapped_column(Text)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

# Annotations and alternative implementations (document-only, commented out).
# Do NOT uncomment or modify the real classes above; these examples are
# illustrative alternatives and optional helper patterns that could be
# used instead of the current table/class layout. They are intentionally
# commented out so they do not change runtime behavior.
# Alternative: Use an association object for `user_roles` to store metadata
# rather than a plain association table. This gives `UserRole` its own model
# and allows easier querying, validation, and additional columns.
#
# class UserRole(Base):
#     __tablename__ = "user_roles"
#     user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
#     role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
#     granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
#     granted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
#
#     user: Mapped["User"] = relationship("User", back_populates="user_roles_assoc")
#     role: Mapped["Role"] = relationship("Role", back_populates="user_roles_assoc")
#
# Then in `User` and `Role` you would use `relationship("UserRole")` instead
# of a secondary table. This is useful when the association has its own lifecycle
# or additional attributes.

# Alternative: Use an Enum for `otp_type` for stricter typing and DB-level
# constraint support. This provides a clearer contract for allowed OTP kinds.
#
# from sqlalchemy import Enum as SAEnum
# import enum
#
# class OtpType(enum.Enum):
#     LOGIN = "login"
#     PASSWORD_RESET = "password_reset"
#     MFA = "mfa"
#
# class OtpVerificationAlt(Base):
#     __tablename__ = "otp_verifications"
#     id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
#     otp_code: Mapped[str] = mapped_column(String(8), nullable=False)
#     otp_type: Mapped[OtpType] = mapped_column(SAEnum(OtpType, name="otp_type_enum"), nullable=False)
#     is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
#     expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
#     created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

# Example alternative helper functions (commented out):
# These are utility patterns often attached to models or to a service layer.
# They are commented out to avoid changing runtime behavior.
#
# def hash_password(password: str) -> str:
#     """Alternative: centralize password hashing using passlib or bcrypt.
#
#     Using a dedicated helper keeps hashing choices consistent and testable.
#     """
#     from passlib.context import CryptContext
#     pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
#     return pwd_context.hash(password)
#
# def verify_password(plain: str, hashed: str) -> bool:
#     """Alternative: verify using passlib CryptContext.
#     """
#     from passlib.context import CryptContext
#     pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
#     return pwd_context.verify(plain, hashed)

# End of annotations for `db/models/auth.py`.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary=user_roles,
        primaryjoin="User.id == user_roles.c.user_id",
        secondaryjoin="Role.id == user_roles.c.role_id",
        back_populates="users",
    )


# Backend note: Groups related backend data or behavior for a single domain concept.
class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    users: Mapped[list[User]] = relationship(
        "User",
        secondary=user_roles,
        primaryjoin="Role.id == user_roles.c.role_id",
        secondaryjoin="User.id == user_roles.c.user_id",
        back_populates="roles",
    )


# Backend note: Groups related backend data or behavior for a single domain concept.
class OtpVerification(Base):
    __tablename__ = "otp_verifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    otp_code: Mapped[str] = mapped_column(String(8), nullable=False)
    otp_type: Mapped[str] = mapped_column(String(30), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
