"""Google OAuth 認可 CLI。"""

from __future__ import annotations

from google_ical.cli import run_command
from google_ical.config import app_config as config, check_auth_config
from google_ical.content.google.auth import run_oauth_flow
from google_ical.pipeline_log import log_info, log_stage_start, log_stage_success


def main() -> int:
    def _run() -> None:
        log_stage_start("設定読込")
        check_auth_config()
        log_stage_success("設定読込")
        log_stage_start("Google 認可")
        saved_path = run_oauth_flow(
            client_id=config.google_client_id,
            client_secret=config.google_client_secret,
            token_path=config.google_token_path,
        )
        log_stage_success("Google 認可", detail=str(saved_path))
        log_info(f"認可完了: トークンを保存しました ({config.google_token_path})")

    return run_command(_run)
