from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Page(BaseModel):
    page: int = 1
    page_size: int = 20


class Paginated(BaseModel):
    items: list
    total: int
    page: int
    page_size: int


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    roles: list[str] = []
