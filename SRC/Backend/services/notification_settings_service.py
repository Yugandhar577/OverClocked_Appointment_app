from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.db.models.organization import OrganizationNotificationSettings


async def get_or_create(session: AsyncSession, organization_id: UUID | None) -> OrganizationNotificationSettings:
    existing = await session.scalar(
        select(OrganizationNotificationSettings).where(
            OrganizationNotificationSettings.organization_id == organization_id
        )
    )
    if existing:
        return existing
    settings = OrganizationNotificationSettings(organization_id=organization_id)
    session.add(settings)
    await session.flush()
    return settings


async def update(session: AsyncSession, organization_id: UUID | None, payload: dict) -> OrganizationNotificationSettings:
    settings = await get_or_create(session, organization_id)
    for key, value in payload.items():
        if hasattr(settings, key) and key not in ("id", "organization_id", "updated_at"):
            setattr(settings, key, value)
    return settings


def resolve_reminder_hours(
    settings: OrganizationNotificationSettings, appointment_type, channel: str
) -> int | None:
    if channel == "email":
        type_val = appointment_type.reminder_email_hours
        return type_val if type_val is not None else settings.reminder_email_hours
    if channel == "sms":
        type_val = appointment_type.reminder_sms_hours
        return type_val if type_val is not None else settings.reminder_sms_hours
    return None
