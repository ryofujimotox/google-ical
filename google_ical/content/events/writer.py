"""予定 JSON ファイルの書き出し。"""

from __future__ import annotations

import json
import os
from pathlib import Path

from google_ical.content.events.models import CalendarEvent


def save_events_file(path: Path, *, source: str, events: tuple[CalendarEvent, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": source,
        "events": [
            {
                "summary": event.summary,
                "start": event.start,
                "end": event.end,
                **({"description": event.description} if event.description else {}),
                **({"all_day": True} if event.all_day else {}),
            }
            for event in events
        ],
    }
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    tmp_path = path.with_name(f".{path.name}.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
