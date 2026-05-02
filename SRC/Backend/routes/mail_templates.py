from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.core.deps import require_role
from SRC.Backend.db.models import MailTemplate, User
from SRC.Backend.db.session import get_db
from SRC.Backend.schemas.mail_templates import (
    MailTemplateCreate,
    MailTemplateOut,
    MailTemplatePreviewRequest,
    MailTemplatePreviewResponse,
    MailTemplateUpdate,
)
from SRC.Backend.services import mail_template_service
from SRC.Backend.services.template_service import available_placeholders

router = APIRouter(prefix="/organiser/mail-templates", tags=["mail-templates"])


def _out(template: MailTemplate) -> MailTemplateOut:
    return MailTemplateOut.model_validate(
        {
            **template.__dict__,
            "can_edit": not template.is_system_default and template.organization_id is not None,
        }
    )


@router.get("", response_model=list[MailTemplateOut])
async def list_mail_templates(
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    return [_out(t) for t in await mail_template_service.list_templates(session, current_user.organization_id)]


@router.post("", response_model=MailTemplateOut, status_code=status.HTTP_201_CREATED)
async def create_mail_template(
    payload: MailTemplateCreate,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    return _out(await mail_template_service.create(session, current_user.organization_id, payload))


@router.get("/placeholders")
async def get_placeholders(
    _current_user: User = Depends(require_role("organiser", "admin")),
):
    return {"placeholders": available_placeholders()}


@router.get("/{template_id}", response_model=MailTemplateOut)
async def get_mail_template(
    template_id: UUID,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    return _out(await mail_template_service.get(session, template_id, current_user.organization_id))


@router.put("/{template_id}", response_model=MailTemplateOut)
async def update_mail_template(
    template_id: UUID,
    payload: MailTemplateUpdate,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    return _out(await mail_template_service.update(session, template_id, current_user.organization_id, payload))


@router.post("/{template_id}/reset", response_model=MailTemplateOut)
async def reset_mail_template(
    template_id: UUID,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    return _out(await mail_template_service.reset_to_default(session, template_id, current_user.organization_id))


@router.post("/{template_id}/preview", response_model=MailTemplatePreviewResponse)
async def preview_mail_template(
    template_id: UUID,
    payload: MailTemplatePreviewRequest | None = None,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    preview = await mail_template_service.preview(
        session,
        template_id,
        current_user.organization_id,
        payload.sample_appointment_id if payload else None,
    )
    return MailTemplatePreviewResponse(**preview)
