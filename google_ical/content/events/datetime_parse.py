"""アプリ設定の日時文字列の厳密解析。"""

from __future__ import annotations

import re
from datetime import datetime

from google_ical.config import DATETIME_FORMAT

_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")


def parse_strict_jst_datetime(value: str) -> datetime:
    """日時文字列を厳密に解析する（ゼロ埋め必須）。
    例: "2026-06-15T00:00:00" → datetime(2026, 6, 15, 0, 0, 0)
    """
    invalid_message = f"日時は {DATETIME_FORMAT} 形式で指定してください"
    if not _DATETIME_RE.fullmatch(value):
        raise ValueError(invalid_message)
    try:
        parsed = datetime.strptime(value, DATETIME_FORMAT)
    except ValueError as exc:
        raise ValueError(invalid_message) from exc
    if parsed.strftime(DATETIME_FORMAT) != value:
        raise ValueError(invalid_message)
    return parsed


def format_jst_datetime(value: datetime) -> str:
    """datetime をアプリ形式の文字列へ戻す。
    例: datetime(2026, 6, 15, 0, 0, 0) → "2026-06-15T00:00:00"
    """
    return value.strftime(DATETIME_FORMAT)
