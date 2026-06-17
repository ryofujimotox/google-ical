"""content/events/loader.py の単体テスト。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from google_ical.content.events.loader import event_source_from_json_path, load_merged_events
from google_ical.exceptions import EventsError


def test_event_source_from_json_path_uses_stem() -> None:
    assert event_source_from_json_path(Path("/tmp/ical_jsons/gomi.json")) == "gomi"


def test_event_source_from_json_path_rejects_empty_stem() -> None:
    with pytest.raises(EventsError, match="source を決められません"):
        event_source_from_json_path(Path("/tmp/ical_jsons/.json"))


def test_event_source_from_json_path_rejects_non_json_suffix() -> None:
    with pytest.raises(EventsError, match="source を決められません"):
        event_source_from_json_path(Path("/tmp/ical_jsons/gomi.txt"))


def test_load_merged_events_merges_files_in_lexicographic_order(tmp_path) -> None:
    events_dir = tmp_path / "ical_jsons"
    events_dir.mkdir()

    (events_dir / "sample.json").write_text(
        json.dumps(
            {
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
    (events_dir / "gomi.json").write_text(
        json.dumps(
            {
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
    assert merged[0].filename == "gomi.json"
    assert merged[0].source == "gomi"
    assert merged[1].filename == "sample.json"
    assert merged[1].source == "sample"
    assert merged[0].event_id != merged[1].event_id


def test_load_merged_events_ignores_legacy_source_field(tmp_path) -> None:
    events_dir = tmp_path / "ical_jsons"
    events_dir.mkdir()
    (events_dir / "gomi.json").write_text(
        json.dumps(
            {
                "source": "legacy",
                "events": [
                    {
                        "summary": "可燃ごみ",
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

    assert merged[0].source == "gomi"


def test_load_merged_events_rejects_invalid_datetime_format(tmp_path) -> None:
    events_dir = tmp_path / "ical_jsons"
    events_dir.mkdir()
    (events_dir / "invalid.json").write_text(
        json.dumps(
            {
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


def test_load_merged_events_accepts_empty_directory(tmp_path) -> None:
    events_dir = tmp_path / "ical_jsons"
    events_dir.mkdir()

    merged = load_merged_events(events_dir)

    assert merged == ()


def test_load_merged_events_accepts_empty_events_file(tmp_path) -> None:
    events_dir = tmp_path / "ical_jsons"
    events_dir.mkdir()
    (events_dir / "sample.json").write_text(
        json.dumps({"events": []}, ensure_ascii=False),
        encoding="utf-8",
    )

    merged = load_merged_events(events_dir)

    assert merged == ()


def test_load_merged_events_rejects_missing_events_key(tmp_path) -> None:
    events_dir = tmp_path / "ical_jsons"
    events_dir.mkdir()
    (events_dir / "invalid.json").write_text("{}", encoding="utf-8")

    with pytest.raises(EventsError, match="形式が不正"):
        load_merged_events(events_dir)


def test_load_merged_events_rejects_duplicate_internal_id(tmp_path) -> None:
    events_dir = tmp_path / "ical_jsons"
    events_dir.mkdir()
    duplicate_event = {
        "summary": "通院",
        "start": "2026-06-03T10:00:00",
        "end": "2026-06-03T11:00:00",
    }
    (events_dir / "sample.json").write_text(
        json.dumps({"events": [duplicate_event, duplicate_event]}, ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(EventsError, match="内部 ID が重複"):
        load_merged_events(events_dir)
