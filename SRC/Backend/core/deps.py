"""
Backend documentation for `core/deps.py`.

This core utility module centralizes shared backend behavior such as security, dependency injection, errors, or time handling.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from collections.abc import Callable
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.core.errors import AccountDisabledError, InvalidCredentialsError, RoleRequiredError
from SRC.Backend.core.security import decode_token
from SRC.Backend.db.models import Role, User, user_roles
from SRC.Backend.db.session import async_session_factory

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# Backend note: Reads data and shapes it for the caller without mutating booking state unless noted by the implementation.
async def get_user_roles(session: AsyncSession, user_id: UUID) -> list[str]:
    result = await session.execute(
        select(Role.name)
        .select_from(user_roles.join(Role, user_roles.c.role_id == Role.id))
        .where(user_roles.c.user_id == user_id)
    )
    return list(result.scalars().all())


# Function explanation:
# `get_user_roles` queries the DB for role names associated with a user
# via the `user_roles` association table. Returning a list of role names
# makes it convenient for the authorization layer to perform set checks.
#
# Alternative (commented): eager-load roles via the `User` relationship
# or cache role snapshots on the `User` model to avoid repeated joins.
#
# async def get_user_roles_via_user(session: AsyncSession, user_id: UUID) -> list[str]:
#     user = await session.get(User, user_id, options=[selectinload(User.roles)])
#     return [r.name for r in user.roles]


# Backend note: Reads data and shapes it for the caller without mutating booking state unless noted by the implementation.
async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> User:
    try:
        payload = decode_token(token)
        user_id = UUID(payload["sub"])
    except Exception as exc:
        raise InvalidCredentialsError() from exc

    async with async_session_factory() as session:
        user = await session.get(User, user_id)
        if user is None:
            raise InvalidCredentialsError()
        if not user.is_active:
            raise AccountDisabledError()
        user.roles_snapshot = await get_user_roles(session, user.id)
        return user


    # Function explanation:
    # `get_current_user` is a FastAPI dependency that validates an OAuth2
    # bearer token, decodes it to a user id, loads the `User` from the DB, and
    # attaches a `roles_snapshot` for quick authorization checks.
    #
    # Alternative (commented): perform token introspection against a token
    # store or identity provider for immediate revocation support instead of
    # depending solely on self-contained JWTs.
    #
    # async def get_current_user_introspect(token: str = Depends(oauth2_scheme)) -> User:
    #     # Call an introspection endpoint or check a DB table for token validity
    #     payload = introspect_token(token)
    #     user = await session.get(User, UUID(payload['sub']))
    #     return user


# Backend note: Builds an authorization or dependency guard used by protected routes.
def require_role(*allowed_roles: str) -> Callable:
    async def dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        roles = getattr(current_user, "roles_snapshot", [])
        if not set(allowed_roles).intersection(roles):
            raise RoleRequiredError(",".join(allowed_roles))
        return current_user

    return dependency


# Function explanation:
# `require_role` returns a dependency that enforces the presence of at
# least one role from `allowed_roles` on the current user. This is used
# to protect routes using FastAPI dependency injection.
#
# Alternative (commented): implement a decorator-based permission system
# or a policy service that evaluates RBAC/ABAC rules for complex checks.
#
# def require_role_decorator(*allowed_roles: str):
#     def decorator(func):
#         async def wrapper(*args, current_user=Depends(get_current_user), **kwargs):
#             roles = getattr(current_user, 'roles_snapshot', [])
#             if not set(allowed_roles).intersection(roles):
#                 raise RoleRequiredError(','.join(allowed_roles))
#             return await func(*args, **kwargs)
#         return wrapper
#     return decorator
