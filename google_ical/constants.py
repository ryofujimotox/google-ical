"""固定パスとデフォルト値（環境変数で上書きしないもの）。"""

from __future__ import annotations

from pathlib import Path

EVENTS_JSON_DIR = Path("config/events")
GOMI_CONFIG_PATH = Path("config/gomi_config.json")
GOOGLE_TOKEN_PATH = Path("config/google_token.json")
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_EVENT_SOURCE = "manual"
DEFAULT_GOMI_OUTPUT = "gomi.json"
