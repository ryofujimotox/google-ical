"""content/gomi/config.py の設定読込テスト。"""

from __future__ import annotations

import json

import pytest

from google_ical.content.gomi.config import load_gomi_config
from google_ical.exceptions import GomiError


def test_load_gomi_config_rejects_blank_region(tmp_path) -> None:
    path = tmp_path / "gomi_config.json"
    path.write_text(
        json.dumps({"gomi": {"region": "   "}}, ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(GomiError, match="形式が不正"):
        load_gomi_config(path)


def test_load_gomi_config_rejects_blank_pdf_url_override(tmp_path) -> None:
    path = tmp_path / "gomi_config.json"
    path.write_text(
        json.dumps({"gomi": {"region": "東京都〇〇区", "pdf_url_override": "   "}}, ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(GomiError, match="形式が不正"):
        load_gomi_config(path)
