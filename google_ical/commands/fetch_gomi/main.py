"""ゴミ収集日PDFをJSONイベントへ変換する。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date

from google_ical.config import ConfigError, load_config
from google_ical.content.gomi.pipeline import events_from_sources


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ゴミPDFをGoogle Calendar用JSONに変換します")
    parser.add_argument("--year", type=int, help="PDF内の月日へ補う年")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = load_config()
        year = args.year or config.gomi_year or date.today().year
        events = events_from_sources(config.gomi_pdf_sources, year=year)
    except (ConfigError, OSError, ValueError) as exc:
        print(f"ゴミPDF解析エラー: {exc}", file=sys.stderr)
        return 1

    payload = {
        "events": [
            {
                "title": event.title,
                "start": event.start.isoformat(),
                "description": event.description,
                "uid": event.uid,
            }
            for event in events
        ]
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
