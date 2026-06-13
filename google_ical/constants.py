"""固定パスとデフォルト値（環境変数で上書きしないもの）。"""

from __future__ import annotations

from pathlib import Path

EVENTS_JSON_DIR = Path("config/events")
GOMI_CONFIG_PATH = Path("config/gomi_config.json")
GOOGLE_TOKEN_PATH = Path("config/google_token.json")
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
DEFAULT_EVENT_SOURCE = "manual"
DEFAULT_GOMI_OUTPUT = "gomi.json"
GOMI_EVENT_SOURCE = "gomi"
GOOGLE_ICAL_ID_KEY = "google_ical_id"
GOOGLE_ICAL_SOURCE_KEY = "google_ical_source"
JST_TIMEZONE = "Asia/Tokyo"
JST_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
