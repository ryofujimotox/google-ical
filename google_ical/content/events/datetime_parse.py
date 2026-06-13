"""JST 日時文字列の厳密解析。"""

from __future__ import annotations

import re
from datetime import datetime

from google_ical.constants import JST_DATETIME_FORMAT

_JST_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")
_INVALID_DATETIME_MESSAGE = f"日時は {JST_DATETIME_FORMAT} 形式で指定してください"


def parse_strict_jst_datetime(value: str) -> datetime:
    """YYYY-MM-DDTHH:MM:SS（ゼロ埋め必須）だけを受理する。"""
    if not _JST_DATETIME_RE.fullmatch(value):
        raise ValueError(_INVALID_DATETIME_MESSAGE)
    try:
        parsed = datetime.strptime(value, JST_DATETIME_FORMAT)
    except ValueError as exc:
        raise ValueError(_INVALID_DATETIME_MESSAGE) from exc
    if parsed.strftime(JST_DATETIME_FORMAT) != value:
        raise ValueError(_INVALID_DATETIME_MESSAGE)
    return parsed


def format_jst_datetime(value: datetime) -> str:
    return value.strftime(JST_DATETIME_FORMAT)
