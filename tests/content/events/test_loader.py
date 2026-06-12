"""content/events/loader.py の単体テスト。"""

from __future__ import annotations

import json

from google_ical.content.events.loader import load_merged_events


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
