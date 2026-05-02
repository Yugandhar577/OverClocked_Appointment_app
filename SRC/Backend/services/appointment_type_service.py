import uuid
from uuid import UUID

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.config import get_settings
from SRC.Backend.core.errors import NotFoundError, NotOwnerError
from SRC.Backend.db.models import (
    AppointmentQuestion,
    AppointmentType,
    AppointmentTypeReminder,
    AppointmentTypeResource,
    AuditLog,
    BookingRule,
    GeneratedSlot,
    Notification,
    Resource,
    Role,
    User,
    WorkingHour,
    user_roles,
)
from SRC.Backend.services import mail_template_service, slot_generation_service


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
            image_url=payload.image_url,
            video_url=payload.video_url,
            manage_capacity=True,
            max_capacity=1,
            cancel_before_minutes=60,
            reschedule_before_minutes=60,
        )
        session.add(appointment_type)
        await session.flush()
        for attr, template_type in [
            ("booking_email_template_id", "booking_confirmation"),
            ("cancellation_email_template_id", "cancellation"),
            ("reminder_email_template_id", "reminder_email"),
            ("reminder_sms_template_id", "reminder_sms"),
        ]:
            default_template = await mail_template_service.get_default(session, template_type)
            if default_template:
                setattr(appointment_type, attr, default_template.id)
        session.add(AppointmentTypeReminder(appointment_type_id=appointment_type.id, channel="email", hours_before=24))
        session.add(AppointmentTypeReminder(appointment_type_id=appointment_type.id, channel="sms", hours_before=2))
        session.add(BookingRule(appointment_type_id=appointment_type.id, max_bookings_per_slot=1))
        _audit(session, actor, "appointment_type_created", appointment_type.id, {"title": appointment_type.title})
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
    reminders = (
        await session.execute(
            select(AppointmentTypeReminder)
            .where(AppointmentTypeReminder.appointment_type_id == appointment_type_id)
            .order_by(AppointmentTypeReminder.channel.asc(), AppointmentTypeReminder.hours_before.asc())
        )
    ).scalars().all()
    return {
        "appointment_type": appointment_type,
        "resources": list(resources),
        "questions": list(questions),
        "working_hours": list(working_hours),
        "reminders": list(reminders),
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
        old = {
            "title": appointment_type.title,
            "description": appointment_type.description,
            "duration_minutes": appointment_type.duration_minutes,
            "venue": appointment_type.venue,
        }
        appointment_type.title = payload.title
        appointment_type.description = payload.description
        appointment_type.duration_minutes = payload.duration_minutes
        appointment_type.timezone = payload.timezone
        appointment_type.preset_type = payload.preset_type
        appointment_type.resource_type = payload.resource_type
        appointment_type.future_days_limit = payload.future_days_limit
        appointment_type.venue = payload.venue
        appointment_type.confirmation_msg = payload.confirmation_msg
        appointment_type.image_url = payload.image_url
        appointment_type.video_url = payload.video_url
        await _assert_template_access(session, payload.booking_email_template_id, actor, "booking_confirmation")
        await _assert_template_access(session, payload.cancellation_email_template_id, actor, "cancellation")
        await _assert_template_access(session, payload.reminder_email_template_id, actor, "reminder_email")
        await _assert_template_access(session, payload.reminder_sms_template_id, actor, "reminder_sms")
        appointment_type.booking_email_template_id = payload.booking_email_template_id
        appointment_type.cancellation_email_template_id = payload.cancellation_email_template_id
        appointment_type.reminder_email_template_id = payload.reminder_email_template_id
        appointment_type.reminder_sms_template_id = payload.reminder_sms_template_id
        _audit(
            session,
            actor,
            "appointment_type_updated",
            appointment_type_id,
            {
                "old": old,
                "new": {
                    "title": appointment_type.title,
                    "duration_minutes": appointment_type.duration_minutes,
                    "venue": appointment_type.venue,
                },
            },
        )
    return appointment_type


async def replace_resources(session: AsyncSession, appointment_type_id: UUID, payload: list, actor: User) -> list[Resource]:
    async with session.begin():
        appointment_type = await _assert_owner(session, appointment_type_id, actor)
        existing_resources = (
            await session.execute(
                select(Resource)
                .join(AppointmentTypeResource, AppointmentTypeResource.resource_id == Resource.id)
                .where(AppointmentTypeResource.appointment_type_id == appointment_type_id)
            )
        ).scalars().all()
        await session.execute(delete(AppointmentTypeResource).where(AppointmentTypeResource.appointment_type_id == appointment_type_id))
        resources = []
        kept_ids = set()
        for index, row in enumerate(payload):
            resource = None
            if row.id:
                resource = await session.get(Resource, row.id)
                if resource and resource.organiser_id != actor.id:
                    resource = None
            if resource is None and row.user_ref_id:
                resource = await session.scalar(
                    select(Resource).where(
                        Resource.organiser_id == actor.id,
                        Resource.user_ref_id == row.user_ref_id,
                        Resource.resource_type == "human",
                    )
                )
            if resource is None:
                resource = Resource(organiser_id=actor.id)
                session.add(resource)
                await session.flush()
            resource.name = row.name
            resource.resource_type = row.resource_type
            resource.capacity = row.capacity
            resource.timezone = row.timezone
            resource.user_ref_id = row.user_ref_id
            resource.is_active = True
            kept_ids.add(resource.id)
            session.add(
                AppointmentTypeResource(
                    appointment_type_id=appointment_type.id,
                    resource_id=resource.id,
                    priority=row.priority or index + 1,
                )
            )
            resources.append(resource)
        for resource in existing_resources:
            if resource.id not in kept_ids and resource.organiser_id == actor.id:
                resource.is_active = False
        _audit(
            session,
            actor,
            "appointment_type_resources_updated",
            appointment_type_id,
            {"resources": [{"id": str(resource.id), "name": resource.name, "capacity": resource.capacity} for resource in resources]},
        )
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
        appointment_type.allow_invitations = payload.allow_invitations
        appointment_type.display_pictures = payload.display_pictures
        appointment_type.is_paid = payload.is_paid
        appointment_type.price = payload.price
        appointment_type.cancel_before_minutes = payload.cancel_before_minutes
        appointment_type.reschedule_before_minutes = payload.reschedule_before_minutes
        appointment_type.max_capacity = payload.max_per_slot
        appointment_type.future_days_limit = payload.future_days_limit
        appointment_type.assignment_method = payload.assignment_method
        appointment_type.starts_with = payload.starts_with
        appointment_type.slot_type = payload.slot_type
        appointment_type.slot_interval_minutes = payload.slot_interval_minutes

        rule = await session.scalar(select(BookingRule).where(BookingRule.appointment_type_id == appointment_type_id))
        if rule:
            rule.max_bookings_per_slot = payload.max_per_slot
            rule.allow_guest = payload.allow_invitations
            rule.slot_creation_method = payload.slot_type
        else:
            session.add(
                BookingRule(
                    appointment_type_id=appointment_type_id,
                    max_bookings_per_slot=payload.max_per_slot,
                    allow_guest=payload.allow_invitations,
                    slot_creation_method=payload.slot_type,
                )
            )
        _audit(session, actor, "appointment_type_rules_updated", appointment_type_id, payload.model_dump())
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


async def resource_candidates(session: AsyncSession, actor: User, mode: str) -> list[dict]:
    if mode == "user":
        stmt = (
            select(User)
            .join(user_roles, user_roles.c.user_id == User.id)
            .join(Role, Role.id == user_roles.c.role_id)
            .where(User.is_active.is_(True), Role.name.in_(["organiser", "admin"]))
            .order_by(User.full_name.asc())
        )
        if actor.organization_id:
            stmt = stmt.where(User.organization_id == actor.organization_id)
        else:
            stmt = stmt.where(User.id == actor.id)
        users = (await session.execute(stmt)).scalars().unique().all()
        return [
            {
                "id": user.id,
                "name": user.full_name,
                "email": user.email,
                "resource_type": "human",
                "capacity": 1,
                "user_ref_id": user.id,
            }
            for user in users
        ]
    resources = (
        await session.execute(
            select(Resource)
            .where(Resource.organiser_id == actor.id, Resource.is_active.is_(True), Resource.user_ref_id.is_(None))
            .order_by(Resource.created_at.desc(), Resource.name.asc())
        )
    ).scalars().all()
    return [
        {
            "id": resource.id,
            "name": resource.name,
            "resource_type": resource.resource_type,
            "capacity": resource.capacity,
            "user_ref_id": resource.user_ref_id,
        }
        for resource in resources
    ]


async def activity(session: AsyncSession, appointment_type_id: UUID, actor: User) -> list[dict]:
    await _assert_owner_read(session, appointment_type_id, actor)
    logs = (
        await session.execute(
            select(AuditLog, User.full_name)
            .outerjoin(User, User.id == AuditLog.actor_id)
            .where(AuditLog.entity_type == "appointment_type", AuditLog.entity_id == appointment_type_id)
            .order_by(AuditLog.created_at.desc())
            .limit(50)
        )
    ).all()
    return [
        {
            "id": log.id,
            "action": log.action,
            "actor_name": actor_name,
            "message": _audit_message(log),
            "created_at": log.created_at,
        }
        for log, actor_name in logs
    ]


async def add_note(session: AsyncSession, appointment_type_id: UUID, message: str, actor: User) -> dict:
    async with session.begin():
        await _assert_owner(session, appointment_type_id, actor)
        log = _audit(session, actor, "note_added", appointment_type_id, {"message": message})
    return {"id": log.id, "action": log.action, "actor_name": actor.full_name, "message": message, "created_at": log.created_at}


async def send_message(session: AsyncSession, appointment_type_id: UUID, message: str, actor: User) -> dict:
    async with session.begin():
        await _assert_owner(session, appointment_type_id, actor)
        session.add(
            Notification(
                channel="email",
                event_type="organiser_message",
                subject="Appointment update",
                body=message,
                status="queued",
            )
        )
        log = _audit(session, actor, "message_sent", appointment_type_id, {"message": message})
    return {"id": log.id, "action": log.action, "actor_name": actor.full_name, "message": message, "created_at": log.created_at}


async def _assert_owner_read(session: AsyncSession, appointment_type_id: UUID, actor: User) -> AppointmentType:
    return await _assert_owner(session, appointment_type_id, actor)


async def _assert_template_access(session: AsyncSession, template_id: UUID | None, actor: User, template_type: str) -> None:
    if template_id is None:
        return
    template = await mail_template_service.get(session, template_id, actor.organization_id)
    if template.template_type != template_type:
        raise NotFoundError("mail_template")


def _audit(session: AsyncSession, actor: User, action: str, appointment_type_id: UUID, value: dict | None = None) -> AuditLog:
    log = AuditLog(
        actor_id=actor.id,
        action=action,
        entity_type="appointment_type",
        entity_id=appointment_type_id,
        new_value=value or {},
    )
    session.add(log)
    return log


def _audit_message(log: AuditLog) -> str | None:
    if isinstance(log.new_value, dict):
        message = log.new_value.get("message")
        if message:
            return str(message)
        resources = log.new_value.get("resources")
        if resources is not None:
            return f"{len(resources)} resource(s) configured"
        title = log.new_value.get("title")
        if title:
            return str(title)
    return None
