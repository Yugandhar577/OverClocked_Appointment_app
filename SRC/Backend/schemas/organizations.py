"""
Backend documentation for `schemas/organizations.py`.

This schema module defines request/response contracts used by FastAPI and the frontend TypeScript client.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Backend note: Input contract used when creating a backend resource.
class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    domain: str = Field(min_length=1, max_length=120)


# Backend note: Input contract used when updating a backend resource.
class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    domain: str | None = Field(default=None, min_length=1, max_length=120)


# Backend note: Groups related backend data or behavior for a single domain concept.
class OrganizationReportIn(BaseModel):
    notes: str = Field(min_length=1, max_length=4000)


# Backend note: Groups related backend data or behavior for a single domain concept.
class OrganizationListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    domain: str
    status: str
    active_members: int
    created_at: datetime


# Backend note: Groups related backend data or behavior for a single domain concept.
class OrganizationDetailOut(OrganizationListItemOut):
    total_members: int
    active_instances: int
    admin_report_notes: str | None
    updated_at: datetime
