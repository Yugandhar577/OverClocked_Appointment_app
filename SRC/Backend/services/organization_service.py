"""
Backend documentation for `services/organization_service.py`.

This service module owns business rules and database coordination so route handlers and UI code stay simple.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.core.errors import AppError, NotFoundError, OrganizationDomainExistsError
from SRC.Backend.db.models import AppointmentType, Organization, User

ALLOWED_ORG_STATUSES = frozenset({"active", "inactive", "suspended", "flagged", "aborted"})


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
def normalize_domain(domain: str) -> str:
    return domain.strip().lower()


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
def merge_report_notes(previous: str | None, new_note: str) -> str:
    note = new_note.strip()
    if not previous:
        return note
    return f"{previous.rstrip()}\n---\n{note}"


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
async def _domain_taken(session: AsyncSession, domain: str, exclude_id: UUID | None) -> bool:
    stmt = select(Organization.id).where(Organization.domain == domain)
    if exclude_id is not None:
        stmt = stmt.where(Organization.id != exclude_id)
    return (await session.scalar(stmt)) is not None


# Backend note: Collects a filtered collection for API or service consumers while preserving existing response contracts.
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


# Backend note: Reads data and shapes it for the caller without mutating booking state unless noted by the implementation.
async def get_organization(session: AsyncSession, org_id: UUID) -> Organization | None:
    return await session.get(Organization, org_id)


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
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


# Backend note: Creates a new domain record after validation and keeps side effects scoped to this workflow.
async def create_organization(session: AsyncSession, name: str, domain: str) -> Organization:
    key = normalize_domain(domain)
    if await _domain_taken(session, key, None):
        raise OrganizationDomainExistsError()
    org = Organization(name=name.strip(), domain=key, status="active")
    session.add(org)
    await session.flush()
    return org


# Backend note: Updates an existing domain record in place while preserving unrelated data.
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


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
async def set_organization_status(session: AsyncSession, org_id: UUID, status: str) -> Organization:
    if status not in ALLOWED_ORG_STATUSES:
        raise AppError({"detail": "invalid_organization_status", "allowed": sorted(ALLOWED_ORG_STATUSES)})
    org = await session.get(Organization, org_id)
    if not org:
        raise NotFoundError("organization")
    org.status = status
    return org


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
async def append_report(session: AsyncSession, org_id: UUID, notes: str) -> Organization:
    org = await session.get(Organization, org_id)
    if not org:
        raise NotFoundError("organization")
    org.admin_report_notes = merge_report_notes(org.admin_report_notes, notes)
    org.status = "flagged"
    return org
