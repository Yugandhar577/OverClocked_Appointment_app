from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.core.deps import require_role
from SRC.Backend.core.errors import NotFoundError
from SRC.Backend.db.models import User
from SRC.Backend.db.session import get_db
from SRC.Backend.schemas.common import Paginated
from SRC.Backend.schemas.organizations import (
    OrganizationCreate,
    OrganizationDetailOut,
    OrganizationListItemOut,
    OrganizationReportIn,
    OrganizationUpdate,
)
from SRC.Backend.services import organization_service

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=Paginated)
async def list_organizations(
    status: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = Query(default=20, le=100),
    _current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    items, total = await organization_service.list_organizations(session, status, search, page, page_size)
    return Paginated(
        items=[OrganizationListItemOut.model_validate(item).model_dump(mode="json") for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=OrganizationDetailOut)
async def create_organization(
    payload: OrganizationCreate,
    _current_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_db),
):
    async with session.begin():
        org = await organization_service.create_organization(session, payload.name, payload.domain)
    detail = await organization_service.organization_detail_dict(session, org)
    return OrganizationDetailOut.model_validate(detail)


@router.get("/{organization_id}", response_model=OrganizationDetailOut)
async def get_organization(
    organization_id: UUID,
    _current_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_db),
):
    org = await organization_service.get_organization(session, organization_id)
    if not org:
        raise NotFoundError("organization")
    detail = await organization_service.organization_detail_dict(session, org)
    return OrganizationDetailOut.model_validate(detail)


@router.patch("/{organization_id}", response_model=OrganizationDetailOut)
async def patch_organization(
    organization_id: UUID,
    payload: OrganizationUpdate,
    _current_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_db),
):
    async with session.begin():
        org = await organization_service.update_organization(
            session, organization_id, payload.name, payload.domain
        )
    detail = await organization_service.organization_detail_dict(session, org)
    return OrganizationDetailOut.model_validate(detail)


@router.post("/{organization_id}/activate", response_model=OrganizationDetailOut)
async def activate_organization(
    organization_id: UUID,
    _current_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_db),
):
    async with session.begin():
        org = await organization_service.set_organization_status(session, organization_id, "active")
    detail = await organization_service.organization_detail_dict(session, org)
    return OrganizationDetailOut.model_validate(detail)


@router.post("/{organization_id}/deactivate", response_model=OrganizationDetailOut)
async def deactivate_organization(
    organization_id: UUID,
    _current_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_db),
):
    async with session.begin():
        org = await organization_service.set_organization_status(session, organization_id, "inactive")
    detail = await organization_service.organization_detail_dict(session, org)
    return OrganizationDetailOut.model_validate(detail)


@router.post("/{organization_id}/suspend", response_model=OrganizationDetailOut)
async def suspend_organization(
    organization_id: UUID,
    _current_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_db),
):
    async with session.begin():
        org = await organization_service.set_organization_status(session, organization_id, "suspended")
    detail = await organization_service.organization_detail_dict(session, org)
    return OrganizationDetailOut.model_validate(detail)


@router.post("/{organization_id}/abort", response_model=OrganizationDetailOut)
async def abort_organization(
    organization_id: UUID,
    _current_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_db),
):
    async with session.begin():
        org = await organization_service.set_organization_status(session, organization_id, "aborted")
    detail = await organization_service.organization_detail_dict(session, org)
    return OrganizationDetailOut.model_validate(detail)


@router.post("/{organization_id}/report", response_model=OrganizationDetailOut)
async def report_organization(
    organization_id: UUID,
    payload: OrganizationReportIn,
    _current_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_db),
):
    async with session.begin():
        org = await organization_service.append_report(session, organization_id, payload.notes)
    detail = await organization_service.organization_detail_dict(session, org)
    return OrganizationDetailOut.model_validate(detail)
