import logging
import re

logger = logging.getLogger(__name__)

AVAILABLE_PLACEHOLDERS = [
    "customer_name",
    "customer_email",
    "customer_phone",
    "appointment_type",
    "appointment_date",
    "appointment_time",
    "confirmation_code",
    "organization_name",
    "venue",
]

_PLACEHOLDER_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def render(template: str, context: dict[str, str]) -> str:
    def replacer(match: re.Match) -> str:
        key = match.group(1).strip()
        val = context.get(key)
        if val is None:
            logger.debug("Template placeholder not found: %s", key)
            return ""
        return str(val)

    return _PLACEHOLDER_RE.sub(replacer, template)


def build_context(appointment, appointment_type, organization=None, slot=None, extra: dict | None = None) -> dict[str, str]:
    ctx: dict[str, str] = {
        "customer_name": appointment.customer_full_name or "",
        "customer_email": appointment.customer_email or "",
        "customer_phone": appointment.customer_phone or "",
        "appointment_type": appointment_type.title if appointment_type else "",
        "confirmation_code": appointment.confirmation_code or "",
        "organization_name": organization.name if organization else "OverClocked Appointments",
        "venue": (appointment_type.venue or "") if appointment_type else "",
    }
    if slot:
        ctx["appointment_date"] = slot.start_datetime.strftime("%B %d, %Y")
        ctx["appointment_time"] = slot.start_datetime.strftime("%I:%M %p UTC")
    else:
        ctx["appointment_date"] = ""
        ctx["appointment_time"] = ""
    if extra:
        ctx.update(extra)
    return ctx


def available_placeholders() -> list[str]:
    return AVAILABLE_PLACEHOLDERS
