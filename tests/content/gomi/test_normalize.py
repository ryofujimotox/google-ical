"""content/gomi/normalize.py の正規化テスト。"""

from __future__ import annotations

import pytest

from google_ical.config import GOMI_MAX_COVERAGE_MONTHS
from google_ical.content.gomi.normalize import count_event_months, normalize_gomi_events
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

_MULTI_MONTH_EVENTS_JSON = """
[
  {
    "summary": "可燃ごみ",
    "start": "2026-06-03T00:00:00",
    "end": "2026-06-04T00:00:00",
    "all_day": true
  },
  {
    "summary": "不燃ごみ",
    "start": "2026-07-10T00:00:00",
    "end": "2026-07-11T00:00:00",
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


def test_normalize_gomi_events_keeps_multiple_months() -> None:
    events = normalize_gomi_events(_MULTI_MONTH_EVENTS_JSON)

    assert len(events) == 2
    assert count_event_months(events) == 2
    assert {event.start[:7] for event in events} == {"2026-06", "2026-07"}


def test_normalize_gomi_events_rejects_excessive_month_coverage() -> None:
    events = [
        {
            "summary": "可燃ごみ",
            "start": f"2026-{month:02d}-01T00:00:00",
            "end": f"2026-{month:02d}-02T00:00:00",
            "all_day": True,
        }
        for month in range(1, GOMI_MAX_COVERAGE_MONTHS + 2)
    ]
    payload = str(events).replace("'", '"').replace("True", "true")

    with pytest.raises(OpenAIClientError, match="月数が上限を超えています"):
        normalize_gomi_events(payload)
