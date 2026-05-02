from uuid import UUID

from sqlalchemy import delete, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.core.errors import LastAdminProtectedError, NotFoundError, SelfDeactivationForbiddenError
from SRC.Backend.db.models import Appointment, Role, User, user_roles
from SRC.Backend.services.auth_service import ensure_default_roles, get_roles_for_user


async def list_users(
    session: AsyncSession,
    role: str | None,
    is_active: bool | None,
    search: str | None,
    page: int,
    page_size: int,
) -> tuple[list[dict], int]:
    stmt = select(User).order_by(User.created_at.desc(), User.id.desc())
    count_stmt = select(func.count()).select_from(User)
    if is_active is not None:
        stmt = stmt.where(User.is_active.is_(is_active))
        count_stmt = count_stmt.where(User.is_active.is_(is_active))
    if search:
        pattern = f"%{search.lower()}%"
        stmt = stmt.where(func.lower(User.email).like(pattern) | func.lower(User.full_name).like(pattern))
        count_stmt = count_stmt.where(func.lower(User.email).like(pattern) | func.lower(User.full_name).like(pattern))
    if role:
        stmt = stmt.join(user_roles, user_roles.c.user_id == User.id).join(Role, Role.id == user_roles.c.role_id).where(Role.name == role)
        count_stmt = count_stmt.join(user_roles, user_roles.c.user_id == User.id).join(Role, Role.id == user_roles.c.role_id).where(Role.name == role)
    users = (await session.execute(stmt.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    total = await session.scalar(count_stmt)
    items = []
    for user in users:
        items.append({**user.__dict__, "roles": await get_roles_for_user(session, user.id)})
    return items, total or 0


async def set_active(session: AsyncSession, target_user_id: UUID, actor: User, is_active: bool) -> User:
    async with session.begin():
        if target_user_id == actor.id and not is_active:
            raise SelfDeactivationForbiddenError()
        user = await session.get(User, target_user_id)
        if not user:
            raise NotFoundError("user")
        user.is_active = is_active
    return user


async def replace_roles(session: AsyncSession, target_user_id: UUID, roles: list[str], actor: User) -> list[str]:
    async with session.begin():
        await ensure_default_roles(session)
        user = await session.get(User, target_user_id)
        if not user:
            raise NotFoundError("user")
        current_roles = set(await get_roles_for_user(session, target_user_id))
        if "admin" in current_roles and "admin" not in roles:
            admin_count = await session.scalar(
                select(func.count())
                .select_from(user_roles.join(Role, user_roles.c.role_id == Role.id))
                .where(Role.name == "admin")
            )
            if admin_count == 1:
                raise LastAdminProtectedError()
        await session.execute(delete(user_roles).where(user_roles.c.user_id == target_user_id))
        role_rows = (await session.execute(select(Role).where(Role.name.in_(roles)))).scalars().all()
        for role in role_rows:
            await session.execute(insert(user_roles).values(user_id=target_user_id, role_id=role.id, granted_by=actor.id))
    return roles


async def stats(session: AsyncSession) -> dict:
    total_users = await session.scalar(select(func.count()).select_from(User))
    total_appointments = await session.scalar(select(func.count()).select_from(Appointment))
    role_counts = dict(
        (await session.execute(
            select(Role.name, func.count(user_roles.c.user_id))
            .join(user_roles, user_roles.c.role_id == Role.id)
            .group_by(Role.name)
        )).all()
    )
    status_counts = dict((await session.execute(select(Appointment.status, func.count()).group_by(Appointment.status))).all())
    return {
        "total_users": total_users or 0,
        "total_organisers": role_counts.get("organiser", 0),
        "total_customers": role_counts.get("customer", 0),
        "total_appointments": total_appointments or 0,
        "appointments_by_status": status_counts,
    }
