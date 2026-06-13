"""content/events/writer.py の単体テスト。"""

from __future__ import annotations

import json

from google_ical.content.events.models import CalendarEvent
from google_ical.content.events.writer import save_events_file


def test_save_events_file_replaces_atomically(tmp_path) -> None:
    path = tmp_path / "gomi.json"
    path.write_text('{"source":"gomi","events":[{"summary":"旧"}]}\n', encoding="utf-8")
    original = path.read_text(encoding="utf-8")

    events = (
        CalendarEvent(
            summary="可燃ごみ",
            start="2026-06-01T00:00:00",
            end="2026-06-02T00:00:00",
            description=None,
            all_day=True,
        ),
    )

    save_events_file(path, source="gomi", events=events)

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["source"] == "gomi"
    assert payload["events"][0]["summary"] == "可燃ごみ"
    assert original != path.read_text(encoding="utf-8")
