"""content/google_sync.py のイベント変換テスト。"""

from __future__ import annotations

import pytest

from google_ical.constants import JST_TIMEZONE
from google_ical.content.events.models import MergedEvent
from google_ical.content.google_sync import _build_desired_events, _event_to_google_body, _needs_update
from google_ical.exceptions import CalendarSyncError


def test_event_to_google_body_converts_all_day_to_google_date() -> None:
    body = _event_to_google_body(
        MergedEvent(
            event_id="event-id",
            source="gomi",
            filename="gomi.json",
            summary="可燃ごみ",
            start="2026-06-03T00:00:00",
            end="2026-06-04T00:00:00",
            description=None,
            all_day=True,
        ),
    )

    assert body["start"] == {"date": "2026-06-03"}
    assert body["end"] == {"date": "2026-06-04"}
    assert body["extendedProperties"]["private"]["google_ical_id"] == "event-id"
    assert body["extendedProperties"]["private"]["google_ical_source"] == "gomi"


def test_event_to_google_body_converts_timed_event_to_jst_datetime() -> None:
    body = _event_to_google_body(
        MergedEvent(
            event_id="event-id",
            source="manual",
            filename="manual.json",
            summary="通院",
            start="2026-06-03T10:00:00",
            end="2026-06-03T11:00:00",
            description="歯科",
            all_day=False,
        ),
    )

    assert body["start"] == {"dateTime": "2026-06-03T10:00:00", "timeZone": JST_TIMEZONE}
    assert body["end"] == {"dateTime": "2026-06-03T11:00:00", "timeZone": JST_TIMEZONE}
    assert body["description"] == "歯科"


def test_event_to_google_body_uses_empty_description_to_clear_existing_text() -> None:
    body = _event_to_google_body(
        MergedEvent(
            event_id="event-id",
            source="manual",
            filename="manual.json",
            summary="通院",
            start="2026-06-03T10:00:00",
            end="2026-06-03T11:00:00",
            description=None,
            all_day=False,
        ),
    )

    assert body["description"] == ""


def test_needs_update_ignores_unmanaged_private_properties() -> None:
    desired = {
        "summary": "可燃ごみ",
        "start": {"date": "2026-06-03"},
        "end": {"date": "2026-06-04"},
        "extendedProperties": {
            "private": {
                "google_ical_id": "event-id",
                "google_ical_source": "gomi",
            },
        },
    }
    current = {
        **desired,
        "extendedProperties": {
            "private": {
                "google_ical_id": "event-id",
                "google_ical_source": "gomi",
                "other_key": "keep",
            },
        },
    }

    assert _needs_update(current, desired) is False


def test_needs_update_detects_description_clear() -> None:
    desired = {
        "summary": "可燃ごみ",
        "description": "",
        "start": {"date": "2026-06-03"},
        "end": {"date": "2026-06-04"},
        "extendedProperties": {
            "private": {
                "google_ical_id": "event-id",
                "google_ical_source": "gomi",
            },
        },
    }
    current = {**desired, "description": "古い説明"}

    assert _needs_update(current, desired) is True


def test_build_desired_events_rejects_duplicate_internal_id() -> None:
    event = MergedEvent(
        event_id="event-id",
        source="manual",
        filename="manual.json",
        summary="通院",
        start="2026-06-03T10:00:00",
        end="2026-06-03T11:00:00",
        description=None,
        all_day=False,
    )

    with pytest.raises(CalendarSyncError, match="重複"):
        _build_desired_events((event, event))
