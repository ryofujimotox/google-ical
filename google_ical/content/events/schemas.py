"""予定 JSON の Pydantic スキーマ（検証専用）。"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from google_ical.constants import DEFAULT_EVENT_SOURCE
from google_ical.content.events.datetime_parse import format_jst_datetime, parse_strict_jst_datetime


class EventRecordSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    start: str
    end: str
    description: str | None = None
    all_day: bool = False

    @field_validator("summary")
    @classmethod
    def validate_summary_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("summary は空文字列にできません")
        return stripped

    @field_validator("start", "end")
    @classmethod
    def validate_datetime_format(cls, value: str) -> str:
        parsed = parse_strict_jst_datetime(value)
        return format_jst_datetime(parsed)

    @model_validator(mode="after")
    def validate_event_constraints(self) -> Self:
        start = parse_strict_jst_datetime(self.start)
        end = parse_strict_jst_datetime(self.end)
        if end < start:
            raise ValueError("end は start 以降を指定してください")
        if self.all_day:
            if start.time().isoformat() != "00:00:00" or end.time().isoformat() != "00:00:00":
                raise ValueError("終日イベントの start/end は 00:00:00 にしてください")
            if (end.date() - start.date()).days != 1:
                raise ValueError("終日イベントは 1 日分のみ指定できます")
        elif start.date() != end.date():
            raise ValueError("複数日にまたがるイベントは非対応です")
        return self


class EventsFileSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str = DEFAULT_EVENT_SOURCE
    events: list[EventRecordSchema]

    @field_validator("source")
    @classmethod
    def validate_source_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("source は空文字列にできません")
        return stripped
