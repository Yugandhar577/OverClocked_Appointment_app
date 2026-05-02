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


async def get_user_roles(session: AsyncSession, user_id: UUID) -> list[str]:
    result = await session.execute(
        select(Role.name)
        .select_from(user_roles.join(Role, user_roles.c.role_id == Role.id))
        .where(user_roles.c.user_id == user_id)
    )
    return list(result.scalars().all())


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


def require_role(*allowed_roles: str) -> Callable:
    async def dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        roles = getattr(current_user, "roles_snapshot", [])
        if not set(allowed_roles).intersection(roles):
            raise RoleRequiredError(",".join(allowed_roles))
        return current_user

    return dependency
