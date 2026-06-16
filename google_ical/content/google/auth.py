"""Google OAuth トークンの読込・保存。"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from google_ical.config import GOOGLE_TOKEN_PATH
from google_ical.exceptions import GoogleAuthError

SCOPES = ("https://www.googleapis.com/auth/calendar",)
_CONSOLE_REDIRECT_URI = "http://localhost"


def should_use_console_oauth_flow() -> bool:
    """認可コード入力フローを使うか判定する。
    GOOGLE_ICAL_OAUTH_CONSOLE=1、または SSH / headless Linux なら True。
    """
    value = os.getenv("GOOGLE_ICAL_OAUTH_CONSOLE", "").strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    if os.getenv("SSH_CONNECTION") or os.getenv("SSH_TTY"):
        return True
    if sys.platform.startswith("linux") and not os.getenv("DISPLAY") and not os.getenv("WAYLAND_DISPLAY"):
        return True
    return False


def token_path() -> Path:
    """OAuth トークンファイルのパスを返す。
    例: → Path("config/google_token.json")
    """
    return GOOGLE_TOKEN_PATH


def ensure_token_file_exists(path: Path | None = None) -> Path:
    """トークンファイルの存在を確認する。無ければ GoogleAuthError。
    例: → Path("config/google_token.json")
    """
    resolved = path or token_path()
    if not resolved.is_file():
        raise GoogleAuthError(
            "Google トークンがありません。python -m google_ical.commands.auth を実行してください",
        )
    return resolved


def load_token_json(path: Path | None = None) -> dict[str, object]:
    """保存済みトークン JSON を読み込む。"""
    resolved = ensure_token_file_exists(path)
    try:
        return json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GoogleAuthError(f"Google トークンの読込に失敗しました: {resolved}") from exc


def save_token_json(token_data: dict[str, object], path: Path | None = None) -> Path:
    """トークン JSON を原子的に保存する（権限 0600）。
    例: {"token": ...} → config/google_token.json
    """
    resolved = path or token_path()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(token_data, ensure_ascii=False, indent=2) + "\n"
    tmp_path = resolved.with_name(f".{resolved.name}.tmp")
    try:
        fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, resolved)
        os.chmod(resolved, 0o600)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
    return resolved


def load_calendar_credentials(path: Path | None = None) -> object:
    """保存済みトークンから Credentials を返す（期限切れなら refresh）。
    例: config/google_token.json → google.oauth2.credentials.Credentials
    """
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
    """Google OAuth 認可を実行し、トークンを保存する。
    ブラウザ認可を試し、headless なら認可コード入力へ切り替える。
    例: → Path("config/google_token.json")
    """
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_config(
        _client_config(client_id=client_id, client_secret=client_secret),
        scopes=SCOPES,
    )

    if should_use_console_oauth_flow():
        credentials = _run_console_flow(flow)
    else:
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
            "redirect_uris": [_CONSOLE_REDIRECT_URI],
        },
    }


def _run_console_flow(flow: object) -> object:
    if hasattr(flow, "run_console"):
        return flow.run_console(access_type="offline", prompt="consent")

    flow.redirect_uri = _console_redirect_uri(flow)
    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
    print("次のURLをブラウザで開いて認可コードを入力してください:")
    print(auth_url)
    code = input("認可コード: ").strip()
    flow.fetch_token(code=code)
    return flow.credentials


def _console_redirect_uri(flow: object) -> str:
    """認可コード入力フロー用の redirect URI（client secrets と一致させる）。"""
    client_config = getattr(flow, "client_config", None)
    if isinstance(client_config, dict):
        redirect_uris = client_config.get("redirect_uris")
        if isinstance(redirect_uris, list) and redirect_uris:
            return str(redirect_uris[0])
    return _CONSOLE_REDIRECT_URI
