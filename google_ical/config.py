"""環境変数からバッチ設定を作る。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(_path: object = None) -> bool:
        """python-dotenv未導入時の最小.env読み込み。"""

        if _path is None:
            return False
        path = Path(_path)
        if not path.exists():
            return False
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\'\""))
        return True


@dataclass(frozen=True)
class AppConfig:
    """Google Calendar 同期に必要な設定。"""

    google_service_account_file: Path
    google_calendar_id: str
    event_json_paths: tuple[Path, ...]
    gomi_pdf_sources: tuple[str, ...]
    gomi_year: int | None
    sync_days: int
    sync_namespace: str


class ConfigError(ValueError):
    """設定不足や型変換失敗を日本語で伝える例外。"""


def _split_csv(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _required(env: Mapping[str, str], key: str) -> str:
    value = env.get(key, "").strip()
    if not value:
        raise ConfigError(f"必須環境変数 {key} が設定されていません")
    return value


def _optional_int(env: Mapping[str, str], key: str) -> int | None:
    value = env.get(key, "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigError(f"環境変数 {key} は整数で指定してください: {value}") from exc


def _positive_int(env: Mapping[str, str], key: str, default: int) -> int:
    value = env.get(key, str(default)).strip() or str(default)
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ConfigError(f"環境変数 {key} は整数で指定してください: {value}") from exc
    if parsed <= 0:
        raise ConfigError(f"環境変数 {key} は 1 以上で指定してください: {value}")
    return parsed


def load_config(env_file: str | os.PathLike[str] | None = ".env") -> AppConfig:
    """`.env` と環境変数から `AppConfig` を返す。"""

    if env_file is not None:
        load_dotenv(env_file)

    env = os.environ
    service_account_file = Path(_required(env, "GOOGLE_SERVICE_ACCOUNT_FILE"))
    calendar_id = _required(env, "GOOGLE_CALENDAR_ID")
    event_paths = tuple(Path(path) for path in _split_csv(_required(env, "EVENT_JSON_PATHS")))
    if not event_paths:
        raise ConfigError("必須環境変数 EVENT_JSON_PATHS にJSONパスを1件以上指定してください")

    return AppConfig(
        google_service_account_file=service_account_file,
        google_calendar_id=calendar_id,
        event_json_paths=event_paths,
        gomi_pdf_sources=_split_csv(env.get("GOMI_PDF_SOURCES")),
        gomi_year=_optional_int(env, "GOMI_YEAR"),
        sync_days=_positive_int(env, "SYNC_DAYS", 180),
        sync_namespace=env.get("SYNC_NAMESPACE", "google-ical").strip() or "google-ical",
    )
