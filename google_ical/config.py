"""環境変数から設定を読み込む。"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

from google_ical.exceptions import ConfigError

_REPO_ROOT = Path(__file__).resolve().parent.parent

# env 不要の固定値（変更時はここを編集）
DATA_DIR = _REPO_ROOT / "data"
SOURCES_DIR = DATA_DIR / "sources"                               # fetch_gomi が取得 PDF を保存
SOURCE_GOMI_PDF = "gomi.pdf"                                     # ゴミ収集日 PDF 名
ICAL_JSONS_DIR = DATA_DIR / "ical_jsons"                         # iCalJSON の置き場。sync_calendar が *.json を読む
ICAL_JSONS_GOMI = "gomi.json"                                    # fetch_gomi の iCalJSON 出力ファイル名
OAUTH_TOKEN_PATH = DATA_DIR / "auth" / "token.json"              # OAuth トークン。auth が認可後に書き出す
GOOGLE_ICAL_ID_KEY = "google_ical_id"                            # iCalJSON と Google イベントの対応付け用キー名。sync_calendar が付与
GOOGLE_ICAL_SOURCE_KEY = "google_ical_source"                    # 本リポ管理イベントの判別用（google_ical_id とセットで必須）
TIMEZONE = "Asia/Tokyo"                                          # JST
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"                            # iCalJSON の日時文字列形式。
GOMI_MAX_COVERAGE_MONTHS = 12                                    # fetch_gomi が許容する最大月数（暦年・年度 PDF 想定。幻覚対策）

__all__ = [
    "AppConfig",
    "ConfigError",
    "DATA_DIR",
    "DATETIME_FORMAT",
    "SOURCES_DIR",
    "SOURCE_GOMI_PDF",
    "ICAL_JSONS_DIR",
    "ICAL_JSONS_GOMI",
    "GOOGLE_ICAL_ID_KEY",
    "GOOGLE_ICAL_SOURCE_KEY",
    "GOMI_MAX_COVERAGE_MONTHS",
    "OAUTH_TOKEN_PATH",
    "TIMEZONE",
    "app_config",
    "check_auth_config",
    "check_fetch_gomi_config",
    "check_sync_calendar_config",
    "install_app_config",
]

_loaded_app_config: AppConfig | None = None


class _AppConfigAccess:
    """各 check_*_config() / install_app_config() 後に app_config.xxx で参照する。"""

    def __getattr__(self, name: str):
        if _loaded_app_config is None:
            raise ConfigError("設定が読み込まれていません。check_*_config() を先に実行してください。")
        return getattr(_loaded_app_config, name)


app_config = _AppConfigAccess()


@dataclass(frozen=True)
class AppConfig:
    """アプリ共通の設定値（check_*_config でコマンドごとに必須 env を検証する）。"""

    google_client_id: str
    google_client_secret: str
    google_calendar_id: str
    oauth_token_path: Path
    openai_api_key: str
    openai_model: str
    gomi_region: str | None
    gomi_pdf_url_override: str | None
    sources_dir: Path
    sources_gomi_pdf: Path
    ical_jsons_dir: Path
    ical_jsons_gomi: Path


def install_app_config(config: AppConfig) -> None:
    """読み込み済み設定をモジュールへ反映する（テスト用）。"""
    global _loaded_app_config
    _loaded_app_config = config


def check_auth_config(env_file: str | Path | None = None) -> None:
    """auth 用の必須 env を検証し、app_config へ反映する。
    必須: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
    """
    load_dotenv(dotenv_path=env_file)
    _require_env("GOOGLE_CLIENT_ID")
    _require_env("GOOGLE_CLIENT_SECRET")
    install_app_config(_build_app_config())


def check_fetch_gomi_config(env_file: str | Path | None = None) -> None:
    """fetch_gomi 用の必須 env を検証し、app_config へ反映する。
    必須: OPENAI_API_KEY, OPENAI_MODEL。GOMI_REGION は GOMI_PDF_URL_OVERRIDE 未設定時のみ。
    """
    load_dotenv(dotenv_path=env_file)
    _require_env("OPENAI_API_KEY")
    _require_env("OPENAI_MODEL")
    if not _read_env("GOMI_PDF_URL_OVERRIDE"):
        _require_env("GOMI_REGION")
    install_app_config(_build_app_config())


def check_sync_calendar_config(env_file: str | Path | None = None) -> None:
    """sync_calendar 用の必須 env を検証し、app_config へ反映する。
    必須: GOOGLE_CALENDAR_ID, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
    """
    load_dotenv(dotenv_path=env_file)
    _require_env("GOOGLE_CALENDAR_ID")
    _require_env("GOOGLE_CLIENT_ID")
    _require_env("GOOGLE_CLIENT_SECRET")
    install_app_config(_build_app_config())


def _build_app_config() -> AppConfig:
    """現在の環境変数と固定値から AppConfig を組み立てる（検証はしない）。"""
    gomi_pdf_url_override = _read_env("GOMI_PDF_URL_OVERRIDE") or None
    gomi_region = _read_env("GOMI_REGION") or None
    return AppConfig(
        google_client_id=_read_env("GOOGLE_CLIENT_ID"),
        google_client_secret=_read_env("GOOGLE_CLIENT_SECRET"),
        google_calendar_id=_read_env("GOOGLE_CALENDAR_ID"),
        oauth_token_path=OAUTH_TOKEN_PATH,
        openai_api_key=_read_env("OPENAI_API_KEY"),
        openai_model=_read_env("OPENAI_MODEL"),
        gomi_region=gomi_region,
        gomi_pdf_url_override=gomi_pdf_url_override,
        sources_dir=SOURCES_DIR,
        sources_gomi_pdf=SOURCES_DIR / SOURCE_GOMI_PDF,
        ical_jsons_dir=ICAL_JSONS_DIR,
        ical_jsons_gomi=ICAL_JSONS_DIR / ICAL_JSONS_GOMI,
    )


def _read_env(name: str) -> str:
    return os.getenv(name, "").strip()


def _require_env(name: str) -> str:
    value = _read_env(name)
    if not value:
        raise ConfigError(f"環境変数 {name} が未設定です。")
    return value
