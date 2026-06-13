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


def load_calendar_credentials(path: Path | None = None) -> object:
    """保存済みトークンを読み、必要なら refresh して Credentials を返す。"""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    token_file = ensure_token_file_exists(path)
    try:
        credentials = Credentials.from_authorized_user_file(str(token_file), scopes=SCOPES)
    except Exception as exc:
        raise GoogleAuthError(
            "Google トークンを読めません。python -m google_ical.commands.auth を実行してください",
        ) from exc

    if credentials.valid:
        return credentials

    if credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            save_token_json(json.loads(credentials.to_json()), token_file)
        except Exception as exc:
            raise GoogleAuthError("Google トークンの更新に失敗しました") from exc
        return credentials

    raise GoogleAuthError(
        "Google トークンが無効です。python -m google_ical.commands.auth を実行してください",
    )


def run_oauth_flow(*, client_id: str, client_secret: str, token_path: Path) -> Path:
    """ブラウザ認可を試し、失敗時はコンソール入力で認可する。"""
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_config(
        _client_config(client_id=client_id, client_secret=client_secret),
        scopes=SCOPES,
    )

    try:
        credentials = flow.run_local_server(
            host="localhost",
            port=0,
            authorization_prompt_message="認可URLを開いてください: {url}",
            success_message="Google 認可が完了しました。この画面を閉じてください。",
            open_browser=True,
            access_type="offline",
            prompt="consent",
        )
    except Exception:
        credentials = _run_console_flow(flow)

    try:
        token_data = json.loads(credentials.to_json())
        return save_token_json(token_data, token_path)
    except Exception as exc:
        raise GoogleAuthError(f"Google トークンの保存に失敗しました: {token_path}") from exc


def _client_config(*, client_id: str, client_secret: str) -> dict[str, object]:
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        },
    }


def _run_console_flow(flow: object) -> object:
    if hasattr(flow, "run_console"):
        return flow.run_console(access_type="offline", prompt="consent")

    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
    print("次のURLをブラウザで開いて認可コードを入力してください:")
    print(auth_url)
    code = input("認可コード: ").strip()
    flow.fetch_token(code=code)
    return flow.credentials
