"""content/events/schemas.py の単体テスト。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from google_ical.content.events.schemas import EventRecordSchema, EventsFileSchema


def test_event_record_schema_accepts_valid_datetime_range() -> None:
    event = EventRecordSchema(
        summary="通院",
        start="2026-06-03T10:00:00",
        end="2026-06-03T11:00:00",
    )

    assert event.start == "2026-06-03T10:00:00"


def test_event_record_schema_rejects_invalid_datetime_format() -> None:
    with pytest.raises(ValidationError, match="形式"):
        EventRecordSchema(
            summary="通院",
            start="2026/06/03 10:00",
            end="2026-06-03T11:00:00",
        )


def test_event_record_schema_rejects_non_zero_padded_datetime() -> None:
    with pytest.raises(ValidationError, match="形式"):
        EventRecordSchema(
            summary="通院",
            start="2026-6-1T9:00:00",
            end="2026-06-03T11:00:00",
        )


def test_event_record_schema_rejects_end_before_start() -> None:
    with pytest.raises(ValidationError, match="end は start 以降"):
        EventRecordSchema(
            summary="通院",
            start="2026-06-03T11:00:00",
            end="2026-06-03T10:00:00",
        )


def test_event_record_schema_accepts_valid_all_day_event() -> None:
    event = EventRecordSchema(
        summary="可燃ごみ",
        start="2026-06-03T00:00:00",
        end="2026-06-04T00:00:00",
        all_day=True,
    )

    assert event.all_day is True


def test_event_record_schema_rejects_all_day_with_non_midnight_times() -> None:
    with pytest.raises(ValidationError, match="00:00:00"):
        EventRecordSchema(
            summary="可燃ごみ",
            start="2026-06-01T12:00:00",
            end="2026-06-02T00:00:00",
            all_day=True,
        )


def test_event_record_schema_rejects_multi_day_all_day_event() -> None:
    with pytest.raises(ValidationError, match="1 日分のみ"):
        EventRecordSchema(
            summary="可燃ごみ",
            start="2026-06-01T00:00:00",
            end="2026-06-03T00:00:00",
            all_day=True,
        )


def test_event_record_schema_rejects_multi_day_timed_event() -> None:
    with pytest.raises(ValidationError, match="複数日"):
        EventRecordSchema(
            summary="通院",
            start="2026-06-01T22:00:00",
            end="2026-06-02T01:00:00",
        )


def test_events_file_schema_rejects_blank_source() -> None:
    with pytest.raises(ValidationError, match="source は空文字列"):
        EventsFileSchema(
            source="",
            events=[
                EventRecordSchema(
                    summary="通院",
                    start="2026-06-03T10:00:00",
                    end="2026-06-03T11:00:00",
                ),
            ],
        )


def test_events_file_schema_rejects_whitespace_only_source() -> None:
    with pytest.raises(ValidationError, match="source は空文字列"):
        EventsFileSchema(
            source="   ",
            events=[
                EventRecordSchema(
                    summary="通院",
                    start="2026-06-03T10:00:00",
                    end="2026-06-03T11:00:00",
                ),
            ],
        )


def test_event_record_schema_rejects_blank_summary() -> None:
    with pytest.raises(ValidationError, match="summary は空文字列"):
        EventRecordSchema(
            summary="   ",
            start="2026-06-03T10:00:00",
            end="2026-06-03T11:00:00",
        )


def test_events_file_schema_accepts_empty_events() -> None:
    events_file = EventsFileSchema(source="manual", events=[])

    assert events_file.events == []


def test_events_file_schema_requires_events_key() -> None:
    with pytest.raises(ValidationError, match="events"):
        EventsFileSchema.model_validate({"source": "manual"})