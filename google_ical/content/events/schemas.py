"""予定 JSON の Pydantic スキーマ（検証専用）。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from google_ical.constants import DEFAULT_EVENT_SOURCE


class EventRecordSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    start: str
    end: str
    description: str | None = None
    all_day: bool = False


class EventsFileSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str = DEFAULT_EVENT_SOURCE
    events: list[EventRecordSchema] = Field(min_length=1)
