"""
Backend documentation for `routes/admin.py`.

This route module keeps HTTP concerns thin: validate inputs, call service-layer logic, and return typed API responses.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.core.deps import require_role
from SRC.Backend.db.models import User
from SRC.Backend.db.session import get_db
from SRC.Backend.schemas.admin import AdminStatsOut, AdminUserOut, RoleUpdateRequest
from SRC.Backend.schemas.common import Paginated
from SRC.Backend.services import admin_service

router = APIRouter(prefix="/admin", tags=["admin"])


# Backend note: Collects a filtered collection for API or service consumers while preserving existing response contracts.
@router.get("/users", response_model=Paginated)
async def list_users(
    role: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = Query(default=20, le=100),
    current_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_db),
):
    items, total = await admin_service.list_users(session, role, is_active, search, page, page_size)
    return Paginated(items=[AdminUserOut.model_validate(item).model_dump(mode="json") for item in items], total=total, page=page, page_size=page_size)


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.patch("/users/{user_id}/activate", response_model=AdminUserOut)
async def activate_user(
    user_id: UUID,
    current_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_db),
):
    user = await admin_service.set_active(session, user_id, current_user, True)
    from SRC.Backend.services.auth_service import get_roles_for_user

    return AdminUserOut.model_validate({**user.__dict__, "roles": await get_roles_for_user(session, user.id)})


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.patch("/users/{user_id}/deactivate", response_model=AdminUserOut)
async def deactivate_user(
    user_id: UUID,
    current_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_db),
):
    user = await admin_service.set_active(session, user_id, current_user, False)
    from SRC.Backend.services.auth_service import get_roles_for_user

    return AdminUserOut.model_validate({**user.__dict__, "roles": await get_roles_for_user(session, user.id)})


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.patch("/users/{user_id}/roles")
async def replace_roles(
    user_id: UUID,
    payload: RoleUpdateRequest,
    current_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_db),
):
    roles = await admin_service.replace_roles(session, user_id, payload.roles, current_user)
    return {"roles": roles}


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.get("/stats", response_model=AdminStatsOut)
async def stats(
    _current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    return await admin_service.stats(session)
