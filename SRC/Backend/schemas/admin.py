from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    is_verified: bool
    is_active: bool
    timezone: str
    phone: str | None
    created_at: datetime
    roles: list[str]


class RoleUpdateRequest(BaseModel):
    roles: list[str]


class AdminStatsOut(BaseModel):
    total_users: int
    total_organisers: int
    total_customers: int
    total_appointments: int
    appointments_by_status: dict[str, int]
