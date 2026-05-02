"""
Backend documentation for `schemas/admin.py`.

This schema module defines request/response contracts used by FastAPI and the frontend TypeScript client.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# Backend note: Groups related backend data or behavior for a single domain concept.
class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    is_verified: bool
    is_active: bool
    timezone: str
    phone: str | None
    organization_id: UUID | None = None
    created_at: datetime
    roles: list[str]


# Backend note: Input contract used when updating a backend resource.
class RoleUpdateRequest(BaseModel):
    roles: list[str]


# Backend note: Groups related backend data or behavior for a single domain concept.
class AdminStatsOut(BaseModel):
    total_users: int
    total_organisers: int
    total_customers: int
    total_appointments: int
    appointments_by_status: dict[str, int]
