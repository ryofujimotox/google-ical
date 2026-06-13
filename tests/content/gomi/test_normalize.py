"""content/gomi/normalize.py の正規化テスト。"""

from __future__ import annotations

import pytest

from google_ical.content.gomi.normalize import normalize_gomi_events
from google_ical.exceptions import OpenAIClientError

_GOMI_EVENTS_JSON = """
[
  {
    "summary": "不燃ごみ",
    "start": "2026-06-10T00:00:00",
    "end": "2026-06-11T00:00:00",
    "all_day": true
  },
  {
    "summary": "可燃ごみ",
    "start": "2026-06-03T00:00:00",
    "end": "2026-06-04T00:00:00",
    "all_day": true
  }
]
"""


def test_normalize_gomi_events_sorts_in_deterministic_order() -> None:
    events = normalize_gomi_events(_GOMI_EVENTS_JSON)

    assert [event.summary for event in events] == ["可燃ごみ", "不燃ごみ"]
    assert all(event.all_day for event in events)


def test_normalize_gomi_events_is_deterministic_for_same_input() -> None:
    first = normalize_gomi_events(_GOMI_EVENTS_JSON)
    second = normalize_gomi_events(_GOMI_EVENTS_JSON)

    assert first == second


def test_normalize_gomi_events_deduplicates_same_collection_day() -> None:
    events = normalize_gomi_events(
        """
        [
          {
            "summary": "可燃ごみ",
            "start": "2026-06-03T00:00:00",
            "end": "2026-06-04T00:00:00",
            "all_day": true
          },
          {
            "summary": "可燃ごみ",
            "start": "2026-06-03T00:00:00",
            "end": "2026-06-04T00:00:00",
            "all_day": true,
            "description": "重複行"
          }
        ]
        """,
    )

    assert len(events) == 1
    assert events[0].summary == "可燃ごみ"
    assert events[0].description is None


def test_normalize_gomi_events_accepts_events_wrapper_object() -> None:
    events = normalize_gomi_events(f'{{"events": {_GOMI_EVENTS_JSON.strip()} }}')

    assert len(events) == 2


def test_normalize_gomi_events_rejects_missing_all_day() -> None:
    with pytest.raises(OpenAIClientError, match="all_day"):
        normalize_gomi_events(
            """
            [
              {
                "summary": "可燃ごみ",
                "start": "2026-06-03T00:00:00",
                "end": "2026-06-04T00:00:00"
              }
            ]
            """,
        )


def test_normalize_gomi_events_rejects_multi_day_all_day_event() -> None:
    with pytest.raises(OpenAIClientError, match="1 日分のみ"):
        normalize_gomi_events(
            """
            [
              {
                "summary": "可燃ごみ",
                "start": "2026-06-03T00:00:00",
                "end": "2026-06-05T00:00:00",
                "all_day": true
              }
            ]
            """,
        )


def test_normalize_gomi_events_accepts_empty_array() -> None:
    assert normalize_gomi_events("[]") == ()
    assert normalize_gomi_events('{"events": []}') == ()


def test_normalize_gomi_events_filters_events_outside_target_month() -> None:
    events = normalize_gomi_events(_GOMI_EVENTS_JSON, target_month="2026-06")

    assert len(events) == 2

    assert normalize_gomi_events(_GOMI_EVENTS_JSON, target_month="2026-07") == ()


def test_normalize_gomi_events_rejects_invalid_target_month() -> None:
    with pytest.raises(OpenAIClientError, match="target_month"):
        normalize_gomi_events(_GOMI_EVENTS_JSON, target_month="2026/06")
