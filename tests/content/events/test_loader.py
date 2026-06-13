"""content/events/loader.py の単体テスト。"""

from __future__ import annotations

import json

import pytest

from google_ical.content.events.loader import load_merged_events
from google_ical.exceptions import EventsError


def test_load_merged_events_merges_files_in_lexicographic_order(tmp_path) -> None:
    events_dir = tmp_path / "events"
    events_dir.mkdir()

    (events_dir / "b_second.json").write_text(
        json.dumps(
            {
                "source": "manual",
                "events": [
                    {
                        "summary": "後ろ",
                        "start": "2026-06-10T10:00:00",
                        "end": "2026-06-10T11:00:00",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (events_dir / "a_first.json").write_text(
        json.dumps(
            {
                "source": "gomi",
                "events": [
                    {
                        "summary": "前",
                        "all_day": True,
                        "start": "2026-06-02T00:00:00",
                        "end": "2026-06-03T00:00:00",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    merged = load_merged_events(events_dir)

    assert len(merged) == 2
    assert merged[0].filename == "a_first.json"
    assert merged[0].source == "gomi"
    assert merged[1].filename == "b_second.json"
    assert merged[0].event_id != merged[1].event_id


def test_load_merged_events_rejects_invalid_datetime_format(tmp_path) -> None:
    events_dir = tmp_path / "events"
    events_dir.mkdir()
    (events_dir / "invalid.json").write_text(
        json.dumps(
            {
                "source": "manual",
                "events": [
                    {
                        "summary": "通院",
                        "start": "2026/06/03 10:00",
                        "end": "2026-06-03T11:00:00",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(EventsError, match="形式が不正"):
        load_merged_events(events_dir)


def test_load_merged_events_rejects_blank_source(tmp_path) -> None:
    events_dir = tmp_path / "events"
    events_dir.mkdir()
    (events_dir / "invalid.json").write_text(
        json.dumps(
            {
                "source": "",
                "events": [
                    {
                        "summary": "通院",
                        "start": "2026-06-03T10:00:00",
                        "end": "2026-06-03T11:00:00",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(EventsError, match="形式が不正"):
        load_merged_events(events_dir)


def test_load_merged_events_accepts_empty_events_file(tmp_path) -> None:
    events_dir = tmp_path / "events"
    events_dir.mkdir()
    (events_dir / "manual.json").write_text(
        json.dumps({"source": "manual", "events": []}, ensure_ascii=False),
        encoding="utf-8",
    )

    merged = load_merged_events(events_dir)

    assert merged == ()


def test_load_merged_events_rejects_missing_events_key(tmp_path) -> None:
    events_dir = tmp_path / "events"
    events_dir.mkdir()
    (events_dir / "invalid.json").write_text(
        json.dumps({"source": "manual"}, ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(EventsError, match="形式が不正"):
        load_merged_events(events_dir)