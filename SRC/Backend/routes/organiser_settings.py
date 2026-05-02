from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.core.deps import require_role
from SRC.Backend.db.models import User
from SRC.Backend.db.session import get_db
from SRC.Backend.schemas.notification_settings import NotificationSettingsOut, NotificationSettingsUpdate
from SRC.Backend.services import notification_settings_service
from SRC.Backend.services.template_service import available_placeholders

router = APIRouter(prefix="/organiser", tags=["organiser-settings"])


@router.get("/notification-settings", response_model=NotificationSettingsOut)
async def get_notification_settings(
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    async with session.begin():
        settings = await notification_settings_service.get_or_create(session, current_user.organization_id)
    return NotificationSettingsOut.model_validate(settings)


@router.put("/notification-settings", response_model=NotificationSettingsOut)
async def update_notification_settings(
    payload: NotificationSettingsUpdate,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    async with session.begin():
        settings = await notification_settings_service.update(
            session,
            current_user.organization_id,
            payload.model_dump(exclude_none=True),
        )
    return NotificationSettingsOut.model_validate(settings)


@router.get("/notification-settings/placeholders")
async def get_placeholders(
    _current_user: User = Depends(require_role("organiser", "admin")),
):
    return {"placeholders": available_placeholders()}
