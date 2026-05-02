from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.core.deps import get_current_user, require_role
from SRC.Backend.db.models import User
from SRC.Backend.db.session import get_db
from SRC.Backend.schemas.appointment_types import (
    AppointmentTypeCreate,
    AppointmentTypeDetail,
    AppointmentTypeListItem,
    AppointmentTypeOut,
    AppointmentTypeUpdateRules,
    PublishOut,
    QuestionIn,
    ResourceCreate,
    ResourceOut,
    ShareLinkOut,
    WorkingHourIn,
)
from SRC.Backend.schemas.common import Paginated
from SRC.Backend.services import appointment_type_service

router = APIRouter(prefix="/appointment-types", tags=["appointment-types"])


def _detail_response(detail: dict) -> AppointmentTypeDetail:
    appointment_type = detail["appointment_type"]
    data = {
        **appointment_type.__dict__,
        "resources": detail["resources"],
        "questions": detail["questions"],
    }
    return AppointmentTypeDetail.model_validate(data)


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


@router.get("/share/{share_token}", response_model=AppointmentTypeDetail)
async def get_share_detail(share_token: str, session: AsyncSession = Depends(get_db)):
    detail = await appointment_type_service.get_by_share_token(session, share_token)
    return _detail_response(detail)


@router.post("", response_model=AppointmentTypeOut, status_code=status.HTTP_201_CREATED)
async def create_appointment_type(
    payload: AppointmentTypeCreate,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    appointment_type = await appointment_type_service.create(session, payload, current_user)
    return appointment_type


@router.get("/{appointment_type_id}", response_model=AppointmentTypeDetail)
async def get_detail(appointment_type_id: UUID, session: AsyncSession = Depends(get_db)):
    detail = await appointment_type_service.get_detail(session, appointment_type_id)
    return _detail_response(detail)


@router.get("/{appointment_type_id}/resources", response_model=list[ResourceOut])
async def resources(appointment_type_id: UUID, session: AsyncSession = Depends(get_db)):
    detail = await appointment_type_service.get_detail(session, appointment_type_id)
    return detail["resources"]


@router.post("/{appointment_type_id}/resources", response_model=ResourceOut, status_code=status.HTTP_201_CREATED)
async def add_resource(
    appointment_type_id: UUID,
    payload: ResourceCreate,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    return await appointment_type_service.add_resource(session, appointment_type_id, payload, current_user)


@router.post("/{appointment_type_id}/working-hours")
async def replace_working_hours(
    appointment_type_id: UUID,
    payload: list[WorkingHourIn],
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    count = await appointment_type_service.replace_working_hours(session, appointment_type_id, payload, current_user)
    return {"count": count}


@router.post("/{appointment_type_id}/questions")
async def replace_questions(
    appointment_type_id: UUID,
    payload: list[QuestionIn],
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    count = await appointment_type_service.replace_questions(session, appointment_type_id, payload, current_user)
    return {"count": count}


@router.post("/{appointment_type_id}/booking-rules", response_model=AppointmentTypeOut)
async def update_rules(
    appointment_type_id: UUID,
    payload: AppointmentTypeUpdateRules,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    return await appointment_type_service.update_rules(session, appointment_type_id, payload, current_user)


@router.patch("/{appointment_type_id}/publish", response_model=PublishOut)
async def publish(
    appointment_type_id: UUID,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    appointment_type, slots_generated = await appointment_type_service.publish(session, appointment_type_id, current_user)
    return PublishOut(id=appointment_type.id, is_published=appointment_type.is_published, slots_generated=slots_generated)


@router.patch("/{appointment_type_id}/unpublish", response_model=AppointmentTypeOut)
async def unpublish(
    appointment_type_id: UUID,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    return await appointment_type_service.unpublish(session, appointment_type_id, current_user)


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
