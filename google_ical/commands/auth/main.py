"""Google OAuth 認可 CLI。"""

from __future__ import annotations

from google_ical.cli import run_command
from google_ical.config import GOOGLE_TOKEN_PATH, load_auth_config
from google_ical.content.google.auth import run_oauth_flow
from google_ical.pipeline_log import log_info, log_stage_start, log_stage_success


def main() -> int:
    def _run() -> None:
        config = load_auth_config()
        log_stage_start("Google 認可")
        saved_path = run_oauth_flow(
            client_id=config.google_client_id,
            client_secret=config.google_client_secret,
            token_path=GOOGLE_TOKEN_PATH,
        )
        log_stage_success("Google 認可", detail=str(saved_path))
        log_info(f"認可完了: トークンを保存しました ({GOOGLE_TOKEN_PATH})")

    return run_command(_run)
