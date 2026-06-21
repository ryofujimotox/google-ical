"""content/events/datetime_parse.py の単体テスト。"""

from __future__ import annotations

import pytest

from google_ical.content.events.datetime_parse import format_jst_datetime, parse_strict_jst_datetime


def test_parse_strict_jst_datetime_accepts_zero_padded_value() -> None:
    parsed = parse_strict_jst_datetime("2026-06-03T10:00:00")

    assert format_jst_datetime(parsed) == "2026-06-03T10:00:00"


@pytest.mark.parametrize(
    "value",
    (
        "2026-6-1T9:00:00",
        "2026-06-03 10:00:00",
        "2026-06-03T10:00",
        "2026-13-40T25:61:61",
    ),
)
def test_parse_strict_jst_datetime_rejects_invalid_shape(value: str) -> None:
    with pytest.raises(ValueError, match="形式"):
        parse_strict_jst_datetime(value)
