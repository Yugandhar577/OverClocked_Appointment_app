"""
Backend documentation for `schemas/common.py`.

This schema module defines request/response contracts used by FastAPI and the frontend TypeScript client.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


# Backend note: Groups related backend data or behavior for a single domain concept.
class Page(BaseModel):
    page: int = 1
    page_size: int = 20


# Backend note: Groups related backend data or behavior for a single domain concept.
class Paginated(BaseModel):
    items: list
    total: int
    page: int
    page_size: int


# Backend note: Groups related backend data or behavior for a single domain concept.
class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    roles: list[str] = []
