from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    domain: str = Field(min_length=1, max_length=120)


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    domain: str | None = Field(default=None, min_length=1, max_length=120)


class OrganizationReportIn(BaseModel):
    notes: str = Field(min_length=1, max_length=4000)


class OrganizationListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    domain: str
    status: str
    active_members: int
    created_at: datetime


class OrganizationDetailOut(OrganizationListItemOut):
    total_members: int
    active_instances: int
    admin_report_notes: str | None
    updated_at: datetime
