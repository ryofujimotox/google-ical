from __future__ import annotations

from google_ical.content.gomi.pipeline import events_from_text


def test_events_from_text_extracts_gomi_events() -> None:
    text = "6月20日 可燃ごみ\n2026/06/21 資源ごみ・缶\n6月20日 可燃ごみ"

    events = events_from_text(text, year=2026, source="sample.pdf")

    assert [(event.title, event.start.isoformat()) for event in events] == [
        ("可燃ごみ", "2026-06-20"),
        ("缶", "2026-06-21"),
        ("資源ごみ", "2026-06-21"),
    ]


def test_events_from_text_ignores_lines_without_keyword() -> None:
    events = events_from_text("6月20日 休館日", year=2026, source="sample.pdf")

    assert events == []
