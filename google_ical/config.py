"""環境変数から設定を読み込む。"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

from google_ical.constants import (
    DEFAULT_OPENAI_MODEL,
    EVENTS_JSON_DIR,
    GOMI_CONFIG_PATH,
    GOOGLE_TOKEN_PATH,
)
from google_ical.exceptions import ConfigError

__all__ = ["AppConfig", "AuthConfig", "ConfigError", "GOOGLE_TOKEN_PATH", "load_auth_config", "load_config"]


@dataclass(frozen=True)
class AuthConfig:
    """Google OAuth 認可コマンド用の設定値。"""

    google_client_id: str
    google_client_secret: str


@dataclass(frozen=True)
class AppConfig:
    """アプリ全体で使う設定値。"""

    openai_api_key: str
    google_calendar_id: str
    events_json_dir: Path
    gomi_config_path: Path
    google_client_id: str
    google_client_secret: str
    openai_model: str
    debug: bool = False


def load_auth_config(env_file: str | Path | None = None) -> AuthConfig:
    """`.env` から Google OAuth 認可に必要な設定だけを読む。"""
    load_dotenv(dotenv_path=env_file)

    google_client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()

    if not google_client_id:
        raise ConfigError("環境変数 GOOGLE_CLIENT_ID が未設定です。")
    if not google_client_secret:
        raise ConfigError("環境変数 GOOGLE_CLIENT_SECRET が未設定です。")

    return AuthConfig(
        google_client_id=google_client_id,
        google_client_secret=google_client_secret,
    )


def load_config(env_file: str | Path | None = None) -> AppConfig:
    """`.env` を読み込み、必須環境変数を検証した設定を返す。"""
    load_dotenv(dotenv_path=env_file)

    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    google_calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "").strip()
    auth = load_auth_config(env_file=None)

    if not openai_api_key:
        raise ConfigError("環境変数 OPENAI_API_KEY が未設定です。")
    if not google_calendar_id:
        raise ConfigError("環境変数 GOOGLE_CALENDAR_ID が未設定です。")

    events_json_dir = Path(os.getenv("EVENTS_JSON_DIR", "").strip() or str(EVENTS_JSON_DIR))
    gomi_config_path = Path(os.getenv("GOMI_CONFIG_PATH", "").strip() or str(GOMI_CONFIG_PATH))
    openai_model = os.getenv("OPENAI_MODEL", "").strip() or DEFAULT_OPENAI_MODEL

    return AppConfig(
        openai_api_key=openai_api_key,
        google_calendar_id=google_calendar_id,
        events_json_dir=events_json_dir,
        gomi_config_path=gomi_config_path,
        google_client_id=auth.google_client_id,
        google_client_secret=auth.google_client_secret,
        openai_model=openai_model,
        debug=_env_flag_enabled("GOOGLE_ICAL_DEBUG"),
    )


def _env_flag_enabled(name: str) -> bool:
    value = os.getenv(name, "").strip().lower()
    return value in {"1", "true", "yes", "on"}
