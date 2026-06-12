"""Google OAuth トークンの読込・保存。"""

from __future__ import annotations

import json
from pathlib import Path

from google_ical.constants import GOOGLE_TOKEN_PATH
from google_ical.exceptions import GoogleAuthError

SCOPES = ("https://www.googleapis.com/auth/calendar",)


def token_path() -> Path:
    return GOOGLE_TOKEN_PATH


def ensure_token_file_exists(path: Path | None = None) -> Path:
    resolved = path or token_path()
    if not resolved.is_file():
        raise GoogleAuthError(
            "Google トークンがありません。python -m google_ical.commands.auth を実行してください",
        )
    return resolved


def load_token_json(path: Path | None = None) -> dict[str, object]:
    resolved = ensure_token_file_exists(path)
    try:
        return json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GoogleAuthError(f"Google トークンの読込に失敗しました: {resolved}") from exc


def save_token_json(token_data: dict[str, object], path: Path | None = None) -> Path:
    resolved = path or token_path()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(token_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return resolved


def run_oauth_flow(*, client_id: str, client_secret: str, token_path: Path) -> Path:
    raise NotImplementedError("Google OAuth フローは未実装です")
