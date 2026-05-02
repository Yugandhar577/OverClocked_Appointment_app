import uuid
from uuid import UUID

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.config import get_settings
from SRC.Backend.core.errors import NotFoundError, NotOwnerError
from SRC.Backend.db.models import (
    AppointmentQuestion,
    AppointmentType,
    AppointmentTypeResource,
    BookingRule,
    GeneratedSlot,
    Resource,
    User,
    WorkingHour,
)
from SRC.Backend.services import slot_generation_service


async def _assert_owner(session: AsyncSession, appointment_type_id: UUID, actor: User) -> AppointmentType:
    appointment_type = await session.get(AppointmentType, appointment_type_id)
    if not appointment_type:
        raise NotFoundError("appointment_type")
    if appointment_type.organiser_id != actor.id:
        roles = await session.execute(select(User.id).where(User.id == actor.id))
        if "admin" not in getattr(actor, "roles_snapshot", []):
            raise NotOwnerError()
    return appointment_type


async def create(session: AsyncSession, payload, actor: User) -> AppointmentType:
    async with session.begin():
        appointment_type = AppointmentType(
            organiser_id=actor.id,
            title=payload.title,
            description=payload.description,
            duration_minutes=payload.duration_minutes,
            timezone=payload.timezone,
            preset_type=payload.preset_type,
            resource_type=payload.resource_type,
            future_days_limit=payload.future_days_limit,
            share_token=str(uuid.uuid4()),
            venue=payload.venue,
            manage_capacity=True,
            max_capacity=1,
            cancel_before_minutes=60,
            reschedule_before_minutes=60,
        )
        session.add(appointment_type)
        await session.flush()
        session.add(BookingRule(appointment_type_id=appointment_type.id, max_bookings_per_slot=1))
    return appointment_type


async def list_public(session: AsyncSession, published: bool | None, page: int, page_size: int) -> tuple[list[dict], int]:
    stmt = (
        select(AppointmentType, User.full_name.label("organiser_name"))
        .join(User, User.id == AppointmentType.organiser_id)
        .order_by(AppointmentType.created_at.desc(), AppointmentType.id.desc())
    )
    count_stmt = select(func.count()).select_from(AppointmentType)
    if published is not None:
        stmt = stmt.where(AppointmentType.is_published.is_(published))
        count_stmt = count_stmt.where(AppointmentType.is_published.is_(published))
    total = await session.scalar(count_stmt)
    rows = (await session.execute(stmt.offset((page - 1) * page_size).limit(page_size))).all()
    return [
        {
            "id": appt_type.id,
            "title": appt_type.title,
            "duration_minutes": appt_type.duration_minutes,
            "is_paid": appt_type.is_paid,
            "price": appt_type.price,
            "organiser_name": organiser_name,
            "preset_type": appt_type.preset_type,
        }
        for appt_type, organiser_name in rows
    ], total or 0


async def get_detail(session: AsyncSession, appointment_type_id: UUID) -> dict:
    appointment_type = await session.get(AppointmentType, appointment_type_id)
    if not appointment_type:
        raise NotFoundError("appointment_type")
    resources = (
        await session.execute(
            select(Resource)
            .join(AppointmentTypeResource, AppointmentTypeResource.resource_id == Resource.id)
            .where(AppointmentTypeResource.appointment_type_id == appointment_type_id)
            .order_by(AppointmentTypeResource.priority.asc(), Resource.created_at.asc())
        )
    ).scalars().all()
    questions = (
        await session.execute(
            select(AppointmentQuestion)
            .where(AppointmentQuestion.appointment_type_id == appointment_type_id)
            .order_by(AppointmentQuestion.display_order.asc())
        )
    ).scalars().all()
    working_hours = (
        await session.execute(
            select(WorkingHour)
            .where(WorkingHour.appointment_type_id == appointment_type_id)
            .order_by(WorkingHour.day_of_week.asc(), WorkingHour.start_time.asc())
        )
    ).scalars().all()
    return {
        "appointment_type": appointment_type,
        "resources": list(resources),
        "questions": list(questions),
        "working_hours": list(working_hours),
    }


async def get_by_share_token(session: AsyncSession, share_token: str) -> dict:
    appointment_type = await session.scalar(select(AppointmentType).where(AppointmentType.share_token == share_token))
    if not appointment_type:
        raise NotFoundError("appointment_type")
    return await get_detail(session, appointment_type.id)


async def add_resource(session: AsyncSession, appointment_type_id: UUID, payload, actor: User) -> Resource:
    async with session.begin():
        appointment_type = await session.get(AppointmentType, appointment_type_id)
        if not appointment_type:
            raise NotFoundError("appointment_type")
        if appointment_type.organiser_id != actor.id and "admin" not in getattr(actor, "roles_snapshot", []):
            raise NotOwnerError()
        resource = Resource(
            organiser_id=actor.id,
            name=payload.name,
            resource_type=payload.resource_type,
            capacity=payload.capacity,
            timezone=payload.timezone,
        )
        session.add(resource)
        await session.flush()
        session.add(
            AppointmentTypeResource(
                appointment_type_id=appointment_type_id,
                resource_id=resource.id,
                priority=payload.priority,
            )
        )
    return resource


async def update_details(session: AsyncSession, appointment_type_id: UUID, payload, actor: User) -> AppointmentType:
    async with session.begin():
        appointment_type = await _assert_owner(session, appointment_type_id, actor)
        appointment_type.title = payload.title
        appointment_type.description = payload.description
        appointment_type.duration_minutes = payload.duration_minutes
        appointment_type.timezone = payload.timezone
        appointment_type.preset_type = payload.preset_type
        appointment_type.resource_type = payload.resource_type
        appointment_type.future_days_limit = payload.future_days_limit
        appointment_type.venue = payload.venue
        appointment_type.confirmation_msg = payload.confirmation_msg
    return appointment_type


async def replace_resources(session: AsyncSession, appointment_type_id: UUID, payload: list, actor: User) -> list[Resource]:
    async with session.begin():
        appointment_type = await _assert_owner(session, appointment_type_id, actor)
        await session.execute(delete(AppointmentTypeResource).where(AppointmentTypeResource.appointment_type_id == appointment_type_id))
        resources = []
        for index, row in enumerate(payload):
            resource = Resource(
                organiser_id=actor.id,
                name=row.name,
                resource_type=row.resource_type,
                capacity=row.capacity,
                timezone=row.timezone,
            )
            session.add(resource)
            await session.flush()
            session.add(
                AppointmentTypeResource(
                    appointment_type_id=appointment_type.id,
                    resource_id=resource.id,
                    priority=row.priority or index + 1,
                )
            )
            resources.append(resource)
    return resources


async def replace_working_hours(session: AsyncSession, appointment_type_id: UUID, payload: list, actor: User) -> int:
    async with session.begin():
        appointment_type = await session.get(AppointmentType, appointment_type_id)
        if not appointment_type:
            raise NotFoundError("appointment_type")
        if appointment_type.organiser_id != actor.id and "admin" not in getattr(actor, "roles_snapshot", []):
            raise NotOwnerError()
        await session.execute(delete(WorkingHour).where(WorkingHour.appointment_type_id == appointment_type_id))
        for row in payload:
            session.add(
                WorkingHour(
                    appointment_type_id=appointment_type_id,
                    resource_id=row.resource_id,
                    day_of_week=row.day_of_week,
                    start_time=row.start_time,
                    end_time=row.end_time,
                    is_active=True,
                )
            )
    return len(payload)


async def replace_questions(session: AsyncSession, appointment_type_id: UUID, payload: list, actor: User) -> int:
    async with session.begin():
        appointment_type = await session.get(AppointmentType, appointment_type_id)
        if not appointment_type:
            raise NotFoundError("appointment_type")
        if appointment_type.organiser_id != actor.id and "admin" not in getattr(actor, "roles_snapshot", []):
            raise NotOwnerError()
        await session.execute(delete(AppointmentQuestion).where(AppointmentQuestion.appointment_type_id == appointment_type_id))
        for index, row in enumerate(payload):
            session.add(
                AppointmentQuestion(
                    appointment_type_id=appointment_type_id,
                    question_text=row.label,
                    answer_type=row.question_type,
                    options=row.options,
                    is_mandatory=row.required,
                    display_order=index,
                )
            )
    return len(payload)


async def update_rules(session: AsyncSession, appointment_type_id: UUID, payload, actor: User) -> AppointmentType:
    async with session.begin():
        appointment_type = await session.get(AppointmentType, appointment_type_id)
        if not appointment_type:
            raise NotFoundError("appointment_type")
        if appointment_type.organiser_id != actor.id and "admin" not in getattr(actor, "roles_snapshot", []):
            raise NotOwnerError()
        appointment_type.requires_confirmation = payload.requires_confirmation
        appointment_type.manage_capacity = payload.manage_capacity
        appointment_type.is_paid = payload.is_paid
        appointment_type.price = payload.price
        appointment_type.cancel_before_minutes = payload.cancel_before_minutes
        appointment_type.reschedule_before_minutes = payload.reschedule_before_minutes
        appointment_type.max_capacity = payload.max_per_slot
        appointment_type.future_days_limit = payload.future_days_limit
        appointment_type.assignment_method = payload.assignment_method

        rule = await session.scalar(select(BookingRule).where(BookingRule.appointment_type_id == appointment_type_id))
        if rule:
            rule.max_bookings_per_slot = payload.max_per_slot
        else:
            session.add(BookingRule(appointment_type_id=appointment_type_id, max_bookings_per_slot=payload.max_per_slot))
    return appointment_type


async def publish(session: AsyncSession, appointment_type_id: UUID, actor: User) -> tuple[AppointmentType, int]:
    async with session.begin():
        appointment_type = await session.get(AppointmentType, appointment_type_id)
        if not appointment_type:
            raise NotFoundError("appointment_type")
        if appointment_type.organiser_id != actor.id and "admin" not in getattr(actor, "roles_snapshot", []):
            raise NotOwnerError()
        await slot_generation_service._config_rows(session, appointment_type_id)
        appointment_type.is_published = True
    slots_generated = await slot_generation_service.regenerate(session, appointment_type_id)
    appointment_type = await session.get(AppointmentType, appointment_type_id)
    return appointment_type, slots_generated


async def unpublish(session: AsyncSession, appointment_type_id: UUID, actor: User) -> AppointmentType:
    async with session.begin():
        appointment_type = await session.get(AppointmentType, appointment_type_id)
        if not appointment_type:
            raise NotFoundError("appointment_type")
        if appointment_type.organiser_id != actor.id and "admin" not in getattr(actor, "roles_snapshot", []):
            raise NotOwnerError()
        appointment_type.is_published = False
        await session.execute(
            update(GeneratedSlot)
            .where(
                GeneratedSlot.appointment_type_id == appointment_type_id,
                GeneratedSlot.booked_count == 0,
                GeneratedSlot.start_datetime > func.now(),
            )
            .values(is_blocked=True)
        )
    return appointment_type


def share_link(share_token: str) -> str:
    return f"{get_settings().app_base_url}/book/share/{share_token}"
