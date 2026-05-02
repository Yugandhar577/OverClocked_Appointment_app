"""
Backend documentation for `services/appointment_type_service.py`.

This service module owns business rules and database coordination so route handlers and UI code stay simple.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

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


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
async def _assert_owner(session: AsyncSession, appointment_type_id: UUID, actor: User) -> AppointmentType:
    appointment_type = await session.get(AppointmentType, appointment_type_id)
    if not appointment_type:
        raise NotFoundError("appointment_type")
    if appointment_type.organiser_id != actor.id:
        roles = await session.execute(select(User.id).where(User.id == actor.id))
        if "admin" not in getattr(actor, "roles_snapshot", []):
            raise NotOwnerError()
    return appointment_type


    # Explanation:
    # `_assert_owner` loads the appointment type and checks whether the actor
    # owns it or has admin rights. It centralizes authorization before any
    # mutation logic runs.
    #
    # Alternative (commented): move ownership checks into a reusable policy
    # function so it can be shared across services.
    #
    # async def _assert_owner_policy(...):
    #     pass


# Backend note: Creates a new domain record after validation and keeps side effects scoped to this workflow.
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


# Explanation:
# `create` inserts a new appointment type with default booking-rule values
# and a generated share token, keeping the mutation inside one transaction.
#
# Alternative (commented): derive defaults from a template or preset
# registry instead of hardcoding rule values in the service.
#
# async def create_from_template(...):
#     pass


# Backend note: Collects a filtered collection for API or service consumers while preserving existing response contracts.
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


# Explanation:
# `list_public` returns a paginated public listing of appointment types
# joined with organiser names, optionally filtering by published state.
#
# Alternative (commented): return a denormalized search index response
# or paginate with cursor tokens for large public catalogs.


# Backend note: Reads data and shapes it for the caller without mutating booking state unless noted by the implementation.
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


# Explanation:
# `get_detail` composes the main appointment type row with related
# resources, questions and working hours so the route can return a
# complete payload.
#
# Alternative (commented): split this into multiple read models or a
# dedicated query object to reduce eager-loading overhead.


# Backend note: Reads data and shapes it for the caller without mutating booking state unless noted by the implementation.
async def get_by_share_token(session: AsyncSession, share_token: str) -> dict:
    appointment_type = await session.scalar(select(AppointmentType).where(AppointmentType.share_token == share_token))
    if not appointment_type:
        raise NotFoundError("appointment_type")
    return await get_detail(session, appointment_type.id)


# Explanation:
# `get_by_share_token` resolves an appointment type by its share token
# and then returns the full detail payload.
#
# Alternative (commented): use a signed, expiring share token and look it
# up through a token verifier instead of raw equality on the database.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
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


# Explanation:
# `add_resource` creates a resource and links it to the appointment type
# in one transaction, after owner validation.
#
# Alternative (commented): allow reusing an existing resource id rather
# than creating a new resource row on every call.


# Backend note: Updates an existing domain record in place while preserving unrelated data.
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


# Explanation:
# `update_details` applies editable appointment type fields inside a
# transaction after ownership validation.
#
# Alternative (commented): use a field whitelist diff function so only
# changed fields are applied and audited.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
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


        # Explanation:
        # `replace_resources` clears the current resource links and rebuilds the
        # set from the supplied payload, returning the new resources.
        #
        # Alternative (commented): compute a delta and only add/remove changed
        # resources to reduce churn in audit logs.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
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


        # Explanation:
        # `replace_working_hours` replaces all stored working hours for the type
        # and returns the count of newly inserted rows.
        #
        # Alternative (commented): normalize weekly schedules in a dedicated
        # timetable table with recurrence rules instead of raw rows.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
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


        # Explanation:
        # `replace_questions` deletes existing questions and recreates them from
        # the payload, preserving display order based on enumeration.
        #
        # Alternative (commented): preserve question ids across edits and update
        # rows in place to maintain stable references in analytics or reports.


# Backend note: Updates an existing domain record in place while preserving unrelated data.
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


    # Explanation:
    # `update_rules` changes booking policy fields on the appointment type
    # and keeps the `BookingRule` row synchronized with the max-per-slot value.
    #
    # Alternative (commented): break rules into distinct policy objects for
    # capacity, payment and timing so they can evolve independently.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
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


# Explanation:
# `publish` sets the appointment type live, ensures schedule/config rows
# exist, and regenerates slots after the transaction completes.
#
# Alternative (commented): queue slot generation as a background job so
# publish returns immediately for large schedules.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
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


# Explanation:
# `unpublish` disables public availability and blocks empty future slots
# to prevent new bookings while keeping existing ones intact.
#
# Alternative (commented): archive the appointment type instead of simply
# flipping the published flag, if you need stronger lifecycle separation.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
def share_link(share_token: str) -> str:
    return f"{get_settings().app_base_url}/book/share/{share_token}"


# Explanation:
# `share_link` builds the externally shareable booking URL from the app
# base URL and the appointment type's share token.
#
# Alternative (commented): generate a fully signed URL with expiry or a
# short alias slug instead of exposing the raw token path.
