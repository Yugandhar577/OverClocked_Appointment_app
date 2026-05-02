from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.config import get_settings
from SRC.Backend.db.models import Appointment, AppointmentType, BookingCartQuote, Package, PricingRule, ThemeSettings, User, WaitlistEntry


ADVANCED_FLAG_KEYS = [
    "ENABLE_WAITLIST",
    "ENABLE_BOOKING_CART",
    "ENABLE_VARIABLE_DURATION",
    "ENABLE_RECURRING_BOOKINGS",
    "ENABLE_NO_SHOW_PROTECTION",
    "ENABLE_SMART_ASSIGNMENT",
    "ENABLE_DYNAMIC_PRICING",
    "ENABLE_NOTIFICATION_WORKFLOWS",
    "ENABLE_ADMIN_MANUAL_BOOKING",
    "ENABLE_APPOINTMENT_ANALYTICS",
    "ENABLE_THEME_CUSTOMIZATION",
    "ENABLE_ODOO_STYLE_UI",
]


DEFAULT_THEME = {
    "primaryColor": "#714B67",
    "secondaryColor": "#017E84",
    "accentColor": "#00A09D",
    "backgroundColor": "#FBF7EF",
    "cardColor": "#FFFFFF",
    "borderColor": "#D8DADD",
    "successColor": "#28A745",
    "warningColor": "#F0AD4E",
    "errorColor": "#DC3545",
    "sidebarColor": "#F3F4F6",
    "headerColor": "#FFFFFF",
    "buttonStyle": "solid",
    "roundedness": "8px",
    "mode": "light",
}


def feature_flags() -> dict[str, bool]:
    settings = get_settings()
    return {
        "ENABLE_WAITLIST": settings.enable_waitlist,
        "ENABLE_BOOKING_CART": settings.enable_booking_cart,
        "ENABLE_VARIABLE_DURATION": settings.enable_variable_duration,
        "ENABLE_RECURRING_BOOKINGS": settings.enable_recurring_bookings,
        "ENABLE_NO_SHOW_PROTECTION": settings.enable_no_show_protection,
        "ENABLE_SMART_ASSIGNMENT": settings.enable_smart_assignment,
        "ENABLE_DYNAMIC_PRICING": settings.enable_dynamic_pricing,
        "ENABLE_NOTIFICATION_WORKFLOWS": settings.enable_notification_workflows,
        "ENABLE_ADMIN_MANUAL_BOOKING": settings.enable_admin_manual_booking,
        "ENABLE_APPOINTMENT_ANALYTICS": settings.enable_appointment_analytics,
        "ENABLE_THEME_CUSTOMIZATION": settings.enable_theme_customization,
        "ENABLE_ODOO_STYLE_UI": settings.enable_odoo_style_ui,
    }


async def join_waitlist(session: AsyncSession, *, appointment_type_id: UUID, slot_id: UUID | None, customer: User, notes: str | None) -> WaitlistEntry:
    async with session.begin():
        entry = WaitlistEntry(
            appointment_type_id=appointment_type_id,
            slot_id=slot_id,
            customer_id=customer.id,
            notes=notes,
        )
        session.add(entry)
        await session.flush()
        return entry


async def list_waitlist(session: AsyncSession) -> list[WaitlistEntry]:
    result = await session.execute(select(WaitlistEntry).order_by(WaitlistEntry.created_at.desc()).limit(200))
    return list(result.scalars().all())


async def create_cart_quote(session: AsyncSession, *, items: list[dict], customer: User | None, currency: str) -> BookingCartQuote:
    total_duration = sum(int(item["duration_minutes"]) for item in items)
    prices = [Decimal(str(item["price"])) for item in items if item.get("price") is not None]
    total_price = sum(prices, Decimal("0")) if prices else None
    async with session.begin():
        quote = BookingCartQuote(
            customer_id=customer.id if customer else None,
            items=items,
            total_duration_minutes=total_duration,
            total_price=total_price,
            currency=currency,
        )
        session.add(quote)
        await session.flush()
        return quote


async def estimate_price(
    session: AsyncSession,
    *,
    appointment_type_id: UUID,
    duration_minutes: int | None,
    base_price: Decimal | None,
) -> dict:
    appointment_type = await session.get(AppointmentType, appointment_type_id)
    base = base_price if base_price is not None else Decimal(str(appointment_type.price or 0 if appointment_type else 0))
    result = await session.execute(
        select(PricingRule)
        .where((PricingRule.appointment_type_id == appointment_type_id) | (PricingRule.appointment_type_id.is_(None)))
        .where(PricingRule.is_active.is_(True))
        .order_by(PricingRule.priority.asc())
    )
    total = base
    breakdown = [{"label": "Base price", "amount": str(base)}]
    for rule in result.scalars().all():
        conditions = rule.conditions or {}
        if duration_minutes and conditions.get("duration_min") and duration_minutes < int(conditions["duration_min"]):
            continue
        if duration_minutes and conditions.get("duration_max") and duration_minutes > int(conditions["duration_max"]):
            continue
        amount = Decimal(rule.adjustment_value)
        if rule.adjustment_type == "percent":
            amount = (total * amount) / Decimal("100")
        total += amount
        breakdown.append({"label": rule.name, "amount": str(amount), "type": rule.rule_type})
    return {"base_price": base, "total_price": total, "currency": appointment_type.currency if appointment_type else "INR", "breakdown": breakdown}


async def active_theme(session: AsyncSession) -> dict:
    result = await session.execute(select(ThemeSettings).where(ThemeSettings.is_active.is_(True)).order_by(ThemeSettings.updated_at.desc()).limit(1))
    theme = result.scalar_one_or_none()
    if theme is None:
        return {"id": None, "name": "Odoo Default", "settings": DEFAULT_THEME, "is_default": True}
    return {"id": theme.id, "name": theme.name, "settings": {**DEFAULT_THEME, **theme.settings}, "is_default": False}


async def save_theme(session: AsyncSession, *, name: str, settings: dict) -> ThemeSettings:
    async with session.begin():
        existing = await session.scalar(select(ThemeSettings).where(ThemeSettings.organization_id.is_(None), ThemeSettings.name == name))
        if existing:
            existing.settings = {**DEFAULT_THEME, **settings}
            existing.is_active = True
            theme = existing
        else:
            theme = ThemeSettings(name=name, settings={**DEFAULT_THEME, **settings}, is_active=True)
            session.add(theme)
        await session.flush()
        return theme


async def reset_theme(session: AsyncSession) -> dict:
    async with session.begin():
        result = await session.execute(select(ThemeSettings).where(ThemeSettings.is_active.is_(True)))
        for theme in result.scalars().all():
            theme.is_active = False
    return {"id": None, "name": "Odoo Default", "settings": DEFAULT_THEME, "is_default": True}


async def create_package(session: AsyncSession, payload) -> Package:
    async with session.begin():
        package = Package(**payload.model_dump())
        session.add(package)
        await session.flush()
        return package


async def list_packages(session: AsyncSession) -> list[Package]:
    result = await session.execute(select(Package).order_by(Package.created_at.desc()))
    return list(result.scalars().all())


async def analytics(session: AsyncSession) -> dict:
    total = await session.scalar(select(func.count()).select_from(Appointment))
    completed = await session.scalar(select(func.count()).select_from(Appointment).where(Appointment.status == "completed"))
    cancelled = await session.scalar(select(func.count()).select_from(Appointment).where(Appointment.status == "cancelled"))
    no_shows = await session.scalar(select(func.count()).select_from(Appointment).where(Appointment.status == "no_show"))
    waitlist_total = await session.scalar(select(func.count()).select_from(WaitlistEntry))
    waitlist_accepted = await session.scalar(select(func.count()).select_from(WaitlistEntry).where(WaitlistEntry.status == "accepted"))
    conversion = float(waitlist_accepted or 0) / float(waitlist_total or 1)
    service_rows = await session.execute(
        select(AppointmentType.title, func.count(Appointment.id))
        .join(Appointment, Appointment.appointment_type_id == AppointmentType.id, isouter=True)
        .group_by(AppointmentType.title)
        .order_by(func.count(Appointment.id).desc())
        .limit(10)
    )
    return {
        "total_bookings": total or 0,
        "completed_bookings": completed or 0,
        "cancelled_bookings": cancelled or 0,
        "no_shows": no_shows or 0,
        "waitlist_conversion_rate": conversion,
        "most_booked_services": [{"service": title, "count": count} for title, count in service_rows.all()],
        "peak_booking_hours": [],
        "staff_utilization": [],
    }
