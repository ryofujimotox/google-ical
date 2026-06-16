"""content/google/sync.py のイベント変換テスト。"""

from __future__ import annotations

import pytest

from google_ical.config import GOOGLE_ICAL_ID_KEY, GOOGLE_ICAL_SOURCE_KEY, TIMEZONE, AppConfig
from google_ical.content.events.models import MergedEvent
from google_ical.content.google.sync import (
    _apply_sync,
    _build_desired_events,
    _event_to_google_body,
    _needs_update,
)
from google_ical.exceptions import CalendarSyncError


def test_event_to_google_body_converts_all_day_to_google_date(app_config: AppConfig) -> None:
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
    assert body["extendedProperties"]["private"][GOOGLE_ICAL_ID_KEY] == "event-id"
    assert body["extendedProperties"]["private"][GOOGLE_ICAL_SOURCE_KEY] == "gomi"


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

    assert body["start"] == {"dateTime": "2026-06-03T10:00:00", "timeZone": TIMEZONE}
    assert body["end"] == {"dateTime": "2026-06-03T11:00:00", "timeZone": TIMEZONE}
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


def test_needs_update_ignores_rfc3339_offset_for_timed_events() -> None:
    desired = {
        "summary": "通院",
        "start": {"dateTime": "2026-06-03T10:00:00", "timeZone": TIMEZONE},
        "end": {"dateTime": "2026-06-03T11:00:00", "timeZone": TIMEZONE},
        "extendedProperties": {
            "private": {
                "google_ical_id": "event-id",
                "google_ical_source": "manual",
            },
        },
    }
    current = {
        **desired,
        "start": {"dateTime": "2026-06-03T10:00:00+09:00"},
        "end": {"dateTime": "2026-06-03T11:00:00+09:00"},
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


def test_apply_sync_deletes_vanished_custom_source_event(monkeypatch: pytest.MonkeyPatch) -> None:
    deleted_event_ids: list[str] = []

    def fake_upsert(_service, *, calendar_id, body, existing):
        raise AssertionError("upsert は呼ばれない")

    def tracking_delete(_service, *, calendar_id, event_id):
        deleted_event_ids.append(event_id)

    monkeypatch.setattr("google_ical.content.google.sync.upsert_event", fake_upsert)
    monkeypatch.setattr("google_ical.content.google.sync.delete_event", tracking_delete)

    existing = {
        "vanished-event": {
            "id": "google-custom",
            "summary": "旧カスタム予定",
            "description": "",
            "start": {"date": "2026-06-01"},
            "end": {"date": "2026-06-02"},
            "extendedProperties": {
                "private": {"google_ical_id": "vanished-event", "google_ical_source": "custom"},
            },
        },
    }

    _apply_sync(object(), "cal-id", existing, {})

    assert deleted_event_ids == ["google-custom"]


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


def test_apply_sync_rolls_back_insert_when_delete_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    rollback_event_ids: list[str] = []

    def fake_upsert(_service, *, calendar_id, body, existing):
        if existing is None:
            return "google-new"
        raise AssertionError("update は呼ばれない")

    def tracking_delete(_service, *, calendar_id, event_id):
        if event_id == "google-old":
            raise CalendarSyncError("削除失敗")
        rollback_event_ids.append(event_id)

    monkeypatch.setattr("google_ical.content.google.sync.upsert_event", fake_upsert)
    monkeypatch.setattr("google_ical.content.google.sync.delete_event", tracking_delete)

    existing = {
        "old-event": {
            "id": "google-old",
            "summary": "古い予定",
            "description": "",
            "start": {"date": "2026-06-01"},
            "end": {"date": "2026-06-02"},
            "extendedProperties": {"private": {"google_ical_id": "old-event", "google_ical_source": "gomi"}},
        },
    }
    desired = {
        "new-event": {
            "summary": "新しい予定",
            "description": "",
            "start": {"date": "2026-06-03"},
            "end": {"date": "2026-06-04"},
            "extendedProperties": {"private": {"google_ical_id": "new-event", "google_ical_source": "gomi"}},
        },
    }

    with pytest.raises(CalendarSyncError, match="削除失敗"):
        _apply_sync(object(), "cal-id", existing, desired)

    assert rollback_event_ids == ["google-new"]


def test_apply_sync_does_not_rollback_failed_delete(monkeypatch: pytest.MonkeyPatch) -> None:
    rollback_inserts: list[dict[str, object]] = []

    def fake_upsert(_service, *, calendar_id, body, existing):
        if existing is None:
            rollback_inserts.append(body)
            return "restored"
        raise AssertionError("update は呼ばれない")

    def failing_delete(_service, *, calendar_id, event_id):
        raise CalendarSyncError("削除失敗")

    monkeypatch.setattr("google_ical.content.google.sync.upsert_event", fake_upsert)
    monkeypatch.setattr("google_ical.content.google.sync.delete_event", failing_delete)

    existing = {
        "old-event": {
            "id": "google-old",
            "summary": "古い予定",
            "description": "",
            "start": {"date": "2026-06-01"},
            "end": {"date": "2026-06-02"},
            "extendedProperties": {"private": {"google_ical_id": "old-event", "google_ical_source": "gomi"}},
        },
    }

    with pytest.raises(CalendarSyncError, match="削除失敗"):
        _apply_sync(object(), "cal-id", existing, {})

    assert rollback_inserts == []


def test_apply_sync_does_not_rollback_failed_update(monkeypatch: pytest.MonkeyPatch) -> None:
    rollback_patches: list[dict[str, object]] = []

    def fake_upsert(_service, *, calendar_id, body, existing):
        if existing is not None:
            raise CalendarSyncError("更新失敗")
        raise AssertionError("insert は呼ばれない")

    def fake_delete(_service, *, calendar_id, event_id):
        raise AssertionError("delete は呼ばれない")

    monkeypatch.setattr("google_ical.content.google.sync.upsert_event", fake_upsert)
    monkeypatch.setattr("google_ical.content.google.sync.delete_event", fake_delete)

    existing = {
        "event-id": {
            "id": "google-1",
            "summary": "古い予定",
            "description": "",
            "start": {"date": "2026-06-01"},
            "end": {"date": "2026-06-02"},
            "extendedProperties": {"private": {"google_ical_id": "event-id", "google_ical_source": "gomi"}},
        },
    }
    desired = {
        "event-id": {
            "summary": "新しい予定",
            "description": "",
            "start": {"date": "2026-06-03"},
            "end": {"date": "2026-06-04"},
            "extendedProperties": {"private": {"google_ical_id": "event-id", "google_ical_source": "gomi"}},
        },
    }

    with pytest.raises(CalendarSyncError, match="更新失敗"):
        _apply_sync(object(), "cal-id", existing, desired)

    assert rollback_patches == []
