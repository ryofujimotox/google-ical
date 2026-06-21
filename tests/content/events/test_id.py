"""content/events/models.py の内部 ID 生成テスト。"""

from __future__ import annotations

from google_ical.content.events.models import generate_event_id


def test_generate_event_id_is_deterministic() -> None:
    kwargs = {
        "filename": "sample.json",
        "summary": "歯科医院",
        "start": "2026-06-05T14:00:00",
        "end": "2026-06-05T15:00:00",
    }
    first = generate_event_id(**kwargs)
    second = generate_event_id(**kwargs)

    assert first == second
    assert len(first) == 64


def test_generate_event_id_changes_when_input_changes() -> None:
    base = {
        "filename": "sample.json",
        "summary": "歯科医院",
        "start": "2026-06-05T14:00:00",
        "end": "2026-06-05T15:00:00",
    }
    original = generate_event_id(**base)

    assert original != generate_event_id(**{**base, "summary": "病院"})
    assert original != generate_event_id(**{**base, "filename": "gomi.json"})
