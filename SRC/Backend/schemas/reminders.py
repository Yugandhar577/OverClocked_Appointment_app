from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReminderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    channel: str
    hours_before: int


class ReminderInput(BaseModel):
    channel: str = Field(pattern="^(email|sms)$")
    hours_before: int = Field(ge=0, le=720)


class ReminderListReplace(BaseModel):
    reminders: list[ReminderInput]
