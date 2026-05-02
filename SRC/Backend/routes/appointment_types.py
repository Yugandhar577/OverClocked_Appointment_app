"""
Backend documentation for `routes/appointment_types.py`.

This route module keeps HTTP concerns thin: validate inputs, call service-layer logic, and return typed API responses.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.core.deps import get_current_user, require_role
from SRC.Backend.db.models import User
from SRC.Backend.db.session import get_db
from SRC.Backend.schemas.appointment_types import (
    ActivityCreate,
    ActivityOut,
    AppointmentTypeCreate,
    AppointmentTypeDetail,
    AppointmentTypeListItem,
    AppointmentTypeOut,
    AppointmentTypeUpdate,
    AppointmentTypeUpdateRules,
    PublishOut,
    QuestionIn,
    ResourceCandidateOut,
    ResourceCreate,
    ResourceOut,
    ShareLinkOut,
    WorkingHourIn,
)
from SRC.Backend.schemas.common import Paginated
from SRC.Backend.services import appointment_type_service

router = APIRouter(prefix="/appointment-types", tags=["appointment-types"])


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
def _detail_response(detail: dict) -> AppointmentTypeDetail:
    appointment_type = detail["appointment_type"]
    data = {
        **appointment_type.__dict__,
        "resources": detail["resources"],
        "questions": detail["questions"],
        "working_hours": detail.get("working_hours", []),
    }
    return AppointmentTypeDetail.model_validate(data)


# Explanation:
# `_detail_response` normalizes the service-layer detail payload into the
# `AppointmentTypeDetail` response model by combining the core appointment
# type record with related resources, questions, and working hours.
#
# Alternative (commented): return the service payload directly and let
# the route layer or Pydantic aliases shape the response, reducing manual
# object assembly here.
#
# def _detail_response_raw(detail: dict):
#     return detail


# Backend note: Collects a filtered collection for API or service consumers while preserving existing response contracts.
@router.get("", response_model=Paginated)
async def list_appointment_types(
    published: bool | None = Query(default=True),
    page: int = 1,
    page_size: int = 20,
    session: AsyncSession = Depends(get_db),
):
    items, total = await appointment_type_service.list_public(session, published, page, page_size)
    return Paginated(
        items=[AppointmentTypeListItem(**item).model_dump(mode="json") for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


# Explanation:
# `list_appointment_types` returns a paginated collection of appointment
# types using the service's public-list query and serializes each item into
# a response-friendly shape.
#
# Alternative (commented): expose a cursor-based paginated API for large
# catalogues instead of page/page_size offsets.


# Backend note: Reads data and shapes it for the caller without mutating booking state unless noted by the implementation.
@router.get("/share/{share_token}", response_model=AppointmentTypeDetail)
async def get_share_detail(share_token: str, session: AsyncSession = Depends(get_db)):
    detail = await appointment_type_service.get_by_share_token(session, share_token)
    return _detail_response(detail)


# Explanation:
# `get_share_detail` loads appointment-type details by share token and
# reuses `_detail_response` for consistent output.
#
# Alternative (commented): validate a signed share token and resolve the
# detail from a lightweight cache before hitting the DB.


# Backend note: Creates a new domain record after validation and keeps side effects scoped to this workflow.
@router.post("", response_model=AppointmentTypeOut, status_code=status.HTTP_201_CREATED)
async def create_appointment_type(
    payload: AppointmentTypeCreate,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    appointment_type = await appointment_type_service.create(session, payload, current_user)
    return appointment_type


# Explanation:
# `create_appointment_type` delegates creation to the service layer and
# returns the created appointment type, keeping route logic thin.
#
# Alternative (commented): return a creation envelope that includes the
# new resource ids and a next-step setup hint for the UI.


# Backend note: Reads data and shapes it for the caller without mutating booking state unless noted by the implementation.
@router.get("/{appointment_type_id}", response_model=AppointmentTypeDetail)
async def get_detail(appointment_type_id: UUID, session: AsyncSession = Depends(get_db)):
    detail = await appointment_type_service.get_detail(session, appointment_type_id)
    return _detail_response(detail)


# Explanation:
# `get_detail` fetches a full appointment-type detail payload by id and
# converts it into the public response schema.
#
# Alternative (commented): split this endpoint into separate summary and
# expanded detail endpoints for smaller payloads.


# Backend note: Updates an existing domain record in place while preserving unrelated data.
@router.patch("/{appointment_type_id}", response_model=AppointmentTypeOut)
async def update_appointment_type(
    appointment_type_id: UUID,
    payload: AppointmentTypeUpdate,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    return await appointment_type_service.update_details(session, appointment_type_id, payload, current_user)


# Explanation:
# `update_appointment_type` updates editable fields for the appointment
# type while delegating validation and persistence to the service layer.
#
# Alternative (commented): use JSON Patch or a command-style endpoint for
# more explicit update operations on individual fields.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.get("/configure/resource-candidates", response_model=list[ResourceCandidateOut])
async def resource_candidates(
    mode: str = Query(default="resource"),
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    return await appointment_type_service.resource_candidates(session, current_user, mode)


@router.get("/{appointment_type_id}/resources", response_model=list[ResourceOut])
async def resources(appointment_type_id: UUID, session: AsyncSession = Depends(get_db)):
    detail = await appointment_type_service.get_detail(session, appointment_type_id)
    return detail["resources"]


# Explanation:
# `resources` reads the appointment type detail and returns the embedded
# resource list to the caller.
#
# Alternative (commented): expose a dedicated resource endpoint backed by
# a direct resource query for cheaper read paths.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.post("/{appointment_type_id}/resources", response_model=ResourceOut, status_code=status.HTTP_201_CREATED)
async def add_resource(
    appointment_type_id: UUID,
    payload: ResourceCreate,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    return await appointment_type_service.add_resource(session, appointment_type_id, payload, current_user)


# Explanation:
# `add_resource` attaches a single resource to an appointment type and
# returns the created association detail from the service layer.
#
# Alternative (commented): accept a bulk payload and add multiple resources
# in one call to reduce client round-trips.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.put("/{appointment_type_id}/resources", response_model=list[ResourceOut])
async def replace_resources(
    appointment_type_id: UUID,
    payload: list[ResourceCreate],
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    return await appointment_type_service.replace_resources(session, appointment_type_id, payload, current_user)


# Explanation:
# `replace_resources` swaps the full resource set for an appointment type
# in one operation, making it easy to sync the server state with the UI.
#
# Alternative (commented): support merge semantics with add/remove lists
# instead of replacing the entire resource collection.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.post("/{appointment_type_id}/working-hours")
async def replace_working_hours(
    appointment_type_id: UUID,
    payload: list[WorkingHourIn],
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    count = await appointment_type_service.replace_working_hours(session, appointment_type_id, payload, current_user)
    return {"count": count}


# Explanation:
# `replace_working_hours` writes a new working-hours set and returns the
# count of rows updated or inserted by the service.
#
# Alternative (commented): return the full normalized working-hours set so
# the caller can verify the resulting schedule immediately.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.post("/{appointment_type_id}/questions")
async def replace_questions(
    appointment_type_id: UUID,
    payload: list[QuestionIn],
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    count = await appointment_type_service.replace_questions(session, appointment_type_id, payload, current_user)
    return {"count": count}


# Explanation:
# `replace_questions` updates the intake question list for the appointment
# type and returns the number of records affected.
#
# Alternative (commented): keep stable question ids and patch only changed
# fields so existing analytics references remain valid.


# Backend note: Updates an existing domain record in place while preserving unrelated data.
@router.post("/{appointment_type_id}/booking-rules", response_model=AppointmentTypeOut)
async def update_rules(
    appointment_type_id: UUID,
    payload: AppointmentTypeUpdateRules,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    return await appointment_type_service.update_rules(session, appointment_type_id, payload, current_user)


# Explanation:
# `update_rules` updates booking-rule settings for the appointment type,
# deferring validation and persistence to the service layer.
#
# Alternative (commented): split rules into smaller endpoints (capacity,
# cancellation, payment) to make each concern easier to manage.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.patch("/{appointment_type_id}/publish", response_model=PublishOut)
async def publish(
    appointment_type_id: UUID,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    appointment_type, slots_generated = await appointment_type_service.publish(session, appointment_type_id, current_user)
    return PublishOut(id=appointment_type.id, is_published=appointment_type.is_published, slots_generated=slots_generated)


# Explanation:
# `publish` marks the appointment type as published and triggers slot
# generation; the response reports whether slots were generated.
#
# Alternative (commented): queue slot generation asynchronously and
# return a job id instead of blocking until generation completes.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.patch("/{appointment_type_id}/unpublish", response_model=AppointmentTypeOut)
async def unpublish(
    appointment_type_id: UUID,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    return await appointment_type_service.unpublish(session, appointment_type_id, current_user)


# Explanation:
# `unpublish` removes the appointment type from public availability and
# delegates the state transition to the service layer.
#
# Alternative (commented): add a soft-deprecation flow that keeps the type
# visible to existing bookings while hiding it from new discovery.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.get("/{appointment_type_id}/activity", response_model=list[ActivityOut])
async def activity(
    appointment_type_id: UUID,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    return await appointment_type_service.activity(session, appointment_type_id, current_user)


@router.post("/{appointment_type_id}/notes", response_model=ActivityOut, status_code=status.HTTP_201_CREATED)
async def add_note(
    appointment_type_id: UUID,
    payload: ActivityCreate,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    return await appointment_type_service.add_note(session, appointment_type_id, payload.message, current_user)


@router.post("/{appointment_type_id}/messages", response_model=ActivityOut, status_code=status.HTTP_201_CREATED)
async def send_message(
    appointment_type_id: UUID,
    payload: ActivityCreate,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    return await appointment_type_service.send_message(session, appointment_type_id, payload.message, current_user)


@router.get("/{appointment_type_id}/share-link", response_model=ShareLinkOut)
async def share_link(
    appointment_type_id: UUID,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    detail = await appointment_type_service.get_detail(session, appointment_type_id)
    appointment_type = detail["appointment_type"]
    if appointment_type.organiser_id != current_user.id and "admin" not in getattr(current_user, "roles_snapshot", []):
        from SRC.Backend.core.errors import NotOwnerError

        raise NotOwnerError()
    return ShareLinkOut(url=appointment_type_service.share_link(appointment_type.share_token))


# Explanation:
# `share_link` validates ownership before returning a shareable URL for
# the appointment type, preventing unauthorized link access.
#
# Alternative (commented): issue time-limited signed share links that can
# be revoked or regenerated without changing the underlying token.
