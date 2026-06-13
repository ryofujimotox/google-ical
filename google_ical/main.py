"""設定ファイルを検証する軽量エントリポイント。"""

from __future__ import annotations

import sys

from google_ical.config import ConfigError, load_config


def main() -> int:
    """`.env` が読み込めるかを確認する。"""

    try:
        config = load_config()
    except ConfigError as exc:
        print(f"設定エラー: {exc}", file=sys.stderr)
        return 1

    print("設定を読み込みました")
    print(f"calendar_id={config.google_calendar_id}")
    print(f"event_json_count={len(config.event_json_paths)}")
    print(f"gomi_pdf_count={len(config.gomi_pdf_sources)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
