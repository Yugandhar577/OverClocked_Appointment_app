from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.core.errors import AppError, NotFoundError, OrganizationDomainExistsError
from SRC.Backend.db.models import AppointmentType, Organization, User

ALLOWED_ORG_STATUSES = frozenset({"active", "inactive", "suspended", "flagged", "aborted"})


def normalize_domain(domain: str) -> str:
    return domain.strip().lower()


def merge_report_notes(previous: str | None, new_note: str) -> str:
    note = new_note.strip()
    if not previous:
        return note
    return f"{previous.rstrip()}\n---\n{note}"


async def _domain_taken(session: AsyncSession, domain: str, exclude_id: UUID | None) -> bool:
    stmt = select(Organization.id).where(Organization.domain == domain)
    if exclude_id is not None:
        stmt = stmt.where(Organization.id != exclude_id)
    return (await session.scalar(stmt)) is not None


async def list_organizations(
    session: AsyncSession,
    status: str | None,
    search: str | None,
    page: int,
    page_size: int,
) -> tuple[list[dict], int]:
    stmt = select(Organization).order_by(Organization.created_at.desc(), Organization.id.desc())
    count_stmt = select(func.count()).select_from(Organization)
    if status:
        stmt = stmt.where(Organization.status == status)
        count_stmt = count_stmt.where(Organization.status == status)
    if search:
        pattern = f"%{search.lower()}%"
        stmt = stmt.where(
            func.lower(Organization.name).like(pattern) | func.lower(Organization.domain).like(pattern)
        )
        count_stmt = count_stmt.where(
            func.lower(Organization.name).like(pattern) | func.lower(Organization.domain).like(pattern)
        )
    total = await session.scalar(count_stmt) or 0
    orgs = (await session.execute(stmt.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    ids = [o.id for o in orgs]
    active_by_org: dict[UUID, int] = {}
    if ids:
        rows = (
            await session.execute(
                select(User.organization_id, func.count())
                .where(User.organization_id.in_(ids), User.is_active.is_(True))
                .group_by(User.organization_id)
            )
        ).all()
        active_by_org = {row[0]: row[1] for row in rows if row[0] is not None}
    items = []
    for org in orgs:
        items.append(
            {
                **{c.key: getattr(org, c.key) for c in Organization.__table__.columns},
                "active_members": active_by_org.get(org.id, 0),
            }
        )
    return items, total


async def get_organization(session: AsyncSession, org_id: UUID) -> Organization | None:
    return await session.get(Organization, org_id)


async def organization_detail_dict(session: AsyncSession, org: Organization) -> dict:
    total_members = (
        await session.scalar(select(func.count()).select_from(User).where(User.organization_id == org.id))
    ) or 0
    active_members = (
        await session.scalar(
            select(func.count())
            .select_from(User)
            .where(User.organization_id == org.id, User.is_active.is_(True))
        )
    ) or 0
    active_instances = (
        await session.scalar(
            select(func.count())
            .select_from(AppointmentType)
            .where(
                AppointmentType.organiser_id.in_(select(User.id).where(User.organization_id == org.id)),
                AppointmentType.is_published.is_(True),
            )
        )
    ) or 0
    base = {c.key: getattr(org, c.key) for c in Organization.__table__.columns}
    return {
        **base,
        "active_members": active_members,
        "total_members": total_members,
        "active_instances": active_instances,
    }


async def create_organization(session: AsyncSession, name: str, domain: str) -> Organization:
    key = normalize_domain(domain)
    if await _domain_taken(session, key, None):
        raise OrganizationDomainExistsError()
    org = Organization(name=name.strip(), domain=key, status="active")
    session.add(org)
    await session.flush()
    return org


async def update_organization(session: AsyncSession, org_id: UUID, name: str | None, domain: str | None) -> Organization:
    org = await session.get(Organization, org_id)
    if not org:
        raise NotFoundError("organization")
    if domain is not None:
        key = normalize_domain(domain)
        if key != org.domain and await _domain_taken(session, key, org_id):
            raise OrganizationDomainExistsError()
        org.domain = key
    if name is not None:
        org.name = name.strip()
    return org


async def set_organization_status(session: AsyncSession, org_id: UUID, status: str) -> Organization:
    if status not in ALLOWED_ORG_STATUSES:
        raise AppError({"detail": "invalid_organization_status", "allowed": sorted(ALLOWED_ORG_STATUSES)})
    org = await session.get(Organization, org_id)
    if not org:
        raise NotFoundError("organization")
    org.status = status
    return org


async def append_report(session: AsyncSession, org_id: UUID, notes: str) -> Organization:
    org = await session.get(Organization, org_id)
    if not org:
        raise NotFoundError("organization")
    org.admin_report_notes = merge_report_notes(org.admin_report_notes, notes)
    org.status = "flagged"
    return org
