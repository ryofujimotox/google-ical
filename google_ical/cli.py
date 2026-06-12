"""コマンド CLI の共通終了処理。"""

from __future__ import annotations

from collections.abc import Callable

from google_ical.exceptions import ConfigError, GoogleIcalError
from google_ical.pipeline_log import log_error


def run_command(handler: Callable[[], None]) -> int:
    """handler を実行し、ドメイン例外は日本語メッセージ付きで非 0 終了する。"""
    try:
        handler()
    except ConfigError as exc:
        log_error(f"設定失敗: {exc}")
        return 1
    except GoogleIcalError as exc:
        log_error(str(exc))
        return 1
    except NotImplementedError as exc:
        log_error(str(exc))
        return 1
    except Exception as exc:
        log_error(f"想定外のエラー: {exc}")
        return 1
    return 0
