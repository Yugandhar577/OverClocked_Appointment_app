from types import SimpleNamespace
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.core.errors import ImmutableTemplateError, NotFoundError, NotOwnerError
from SRC.Backend.db.models import Appointment, AppointmentType, GeneratedSlot, MailTemplate, Organization, User
from SRC.Backend.services import template_service


async def list_templates(session: AsyncSession, org_id: UUID | None) -> list[MailTemplate]:
    rows = (
        await session.execute(
            select(MailTemplate)
            .where((MailTemplate.organization_id.is_(None)) | (MailTemplate.organization_id == org_id))
            .order_by(MailTemplate.template_type.asc(), MailTemplate.is_system_default.desc(), MailTemplate.name.asc())
        )
    ).scalars().all()
    return list(rows)


async def get(session: AsyncSession, template_id: UUID, org_id: UUID | None) -> MailTemplate:
    template = await session.get(MailTemplate, template_id)
    if not template:
        raise NotFoundError("mail_template")
    if template.organization_id is not None and template.organization_id != org_id:
        raise NotOwnerError()
    return template


async def get_default(session: AsyncSession, template_type: str) -> MailTemplate | None:
    return await session.scalar(
        select(MailTemplate)
        .where(
            MailTemplate.organization_id.is_(None),
            MailTemplate.template_type == template_type,
            MailTemplate.is_system_default.is_(True),
        )
        .order_by(MailTemplate.created_at.asc())
    )


async def create(session: AsyncSession, org_id: UUID | None, payload) -> MailTemplate:
    if org_id is None:
        raise NotOwnerError()
    async with session.begin():
        template = MailTemplate(
            organization_id=org_id,
            template_type=payload.template_type,
            name=payload.name,
            subject=payload.subject,
            body_html=payload.body_html,
            description=payload.description,
            is_system_default=False,
        )
        session.add(template)
        await session.flush()
    return template


async def update(session: AsyncSession, template_id: UUID, org_id: UUID | None, payload) -> MailTemplate:
    async with session.begin():
        template = await get(session, template_id, org_id)
        if template.is_system_default or template.organization_id is None:
            raise ImmutableTemplateError()
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(template, key, value)
    return template


async def reset_to_default(session: AsyncSession, template_id: UUID, org_id: UUID | None) -> MailTemplate:
    async with session.begin():
        template = await get(session, template_id, org_id)
        if template.is_system_default or template.organization_id is None:
            raise ImmutableTemplateError()
        default = await get_default(session, template.template_type)
        if not default:
            raise NotFoundError("mail_template_default")
        template.subject = default.subject
        template.body_html = default.body_html
        template.description = default.description
    return template


async def preview(
    session: AsyncSession,
    template_id: UUID,
    org_id: UUID | None,
    sample_appointment_id: UUID | None = None,
) -> dict[str, str | None]:
    template = await get(session, template_id, org_id)
    context = await _preview_context(session, org_id, sample_appointment_id)
    return {
        "subject": template_service.render(template.subject or "", context) if template.subject else None,
        "body_html": template_service.render(template.body_html, context),
    }


async def _preview_context(session: AsyncSession, org_id: UUID | None, sample_appointment_id: UUID | None) -> dict[str, str]:
    if sample_appointment_id:
        row = (
            await session.execute(
                select(Appointment, AppointmentType, GeneratedSlot, User, Organization)
                .join(AppointmentType, AppointmentType.id == Appointment.appointment_type_id)
                .join(GeneratedSlot, GeneratedSlot.id == Appointment.slot_id)
                .join(User, User.id == AppointmentType.organiser_id)
                .outerjoin(Organization, Organization.id == User.organization_id)
                .where(Appointment.id == sample_appointment_id)
            )
        ).first()
        if row:
            appointment, appointment_type, slot, organiser, organization = row
            if organiser.organization_id is not None and organiser.organization_id != org_id:
                raise NotOwnerError()
            return template_service.build_context(appointment, appointment_type, organization, slot)

    sample_appointment = SimpleNamespace(
        customer_full_name="John Doe",
        customer_email="john@example.com",
        customer_phone="+91 98765 43210",
        confirmation_code="DEMO123",
    )
    sample_type = SimpleNamespace(title="30-min Consultation", venue="Room 201, VIT Pune")
    sample_org = SimpleNamespace(name="OverClocked")
    return template_service.build_context(
        sample_appointment,
        sample_type,
        sample_org,
        extra={"appointment_date": "May 7, 2026", "appointment_time": "11:00 AM"},
    )
