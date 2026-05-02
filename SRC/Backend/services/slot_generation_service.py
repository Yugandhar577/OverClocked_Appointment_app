"""
Backend documentation for `services/slot_generation_service.py`.

This service module owns business rules and database coordination so route handlers and UI code stay simple.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from uuid import UUID

from sqlalchemy import Select, and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.core.errors import ConfigIncompleteError, NotFoundError
from SRC.Backend.core.time import utcnow
from SRC.Backend.db.models import AppointmentType, AppointmentTypeResource, GeneratedSlot, Resource, WorkingHour


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
async def _config_rows(session: AsyncSession, appointment_type_id: UUID):
    appointment_type = await session.get(AppointmentType, appointment_type_id)
    if not appointment_type:
        raise NotFoundError("appointment_type")
    resources = (
        await session.execute(
            select(Resource)
            .join(AppointmentTypeResource, AppointmentTypeResource.resource_id == Resource.id)
            .where(
                AppointmentTypeResource.appointment_type_id == appointment_type_id,
                Resource.is_active.is_(True),
            )
            .order_by(AppointmentTypeResource.priority.asc(), Resource.created_at.asc())
        )
    ).scalars().all()
    hours = (
        await session.execute(
            select(WorkingHour).where(
                WorkingHour.appointment_type_id == appointment_type_id,
                WorkingHour.is_active.is_(True),
            )
        )
    ).scalars().all()
    missing = []
    if not resources:
        missing.append("resources")
    if not hours:
        missing.append("working_hours")
    if missing:
        raise ConfigIncompleteError(missing)
    return appointment_type, list(resources), list(hours)


# Explanation:
# `_config_rows` loads the appointment type plus its active resources and
# working hours, then validates that the publication prerequisites exist.
#
# Alternative (commented): return a structured config object instead of a
# tuple so the call sites can access named fields more safely.
#
# async def _config_rows_structured(...):
#     pass


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
async def validate_publishable(session: AsyncSession, appointment_type_id: UUID) -> None:
    await _config_rows(session, appointment_type_id)


# Explanation:
# `validate_publishable` is a narrow guard that reuses `_config_rows` to
# confirm the appointment type has enough configuration to publish.
#
# Alternative (commented): return the missing config items so callers can
# present a richer validation message to the user.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
async def regenerate(session: AsyncSession, appointment_type_id: UUID) -> int:
    async with session.begin():
        appointment_type, resources, hours = await _config_rows(session, appointment_type_id)
        local_tz = ZoneInfo(appointment_type.timezone)
        now_utc = utcnow()
        start_date = now_utc.astimezone(local_tz).date()
        inserted = 0
        resource_by_id = {resource.id: resource for resource in resources}
        duration = timedelta(minutes=appointment_type.duration_minutes)
        padding = timedelta(minutes=appointment_type.padding_minutes)

        for offset in range(appointment_type.future_days_limit + 1):
            day = start_date + timedelta(days=offset)
            day_hours = [row for row in hours if row.day_of_week == day.weekday()]
            for window in day_hours:
                target_resources = resources
                if window.resource_id:
                    target = resource_by_id.get(window.resource_id)
                    target_resources = [target] if target else []
                for resource in target_resources:
                    cursor = datetime.combine(day, window.start_time, tzinfo=local_tz)
                    end_local = datetime.combine(day, window.end_time, tzinfo=local_tz)
                    while cursor + duration <= end_local:
                        start_utc = cursor.astimezone(ZoneInfo("UTC"))
                        end_utc = (cursor + duration).astimezone(ZoneInfo("UTC"))
                        cursor = cursor + duration + padding
                        if start_utc < now_utc:
                            continue
                        existing_stmt: Select = select(GeneratedSlot.id).where(
                            and_(
                                GeneratedSlot.appointment_type_id == appointment_type.id,
                                GeneratedSlot.resource_id == resource.id,
                                GeneratedSlot.start_datetime == start_utc,
                            )
                        )
                        existing = await session.scalar(existing_stmt)
                        if existing:
                            continue
                        session.add(
                            GeneratedSlot(
                                appointment_type_id=appointment_type.id,
                                resource_id=resource.id,
                                start_datetime=start_utc,
                                end_datetime=end_utc,
                                max_capacity=resource.capacity if appointment_type.manage_capacity else 1,
                                booked_count=0,
                                is_blocked=False,
                                source="weekly",
                            )
                        )
                        inserted += 1
        return inserted


# Explanation:
# `regenerate` builds generated slots from working hours across the future
# date window, skipping past times and existing slots, then inserts new
# records for each open time block.
#
# Alternative (commented): replace eager generation with on-demand slot
# creation and a cache, which can reduce writes for sparse calendars.
