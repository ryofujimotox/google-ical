"""content/gomi/pipeline.py の source 生成テスト。"""

from __future__ import annotations

from pathlib import Path

import pytest

from google_ical.content.gomi.pipeline import gomi_event_source
from google_ical.exceptions import GomiError


def test_gomi_event_source_uses_output_path_stem() -> None:
    assert gomi_event_source(Path("/tmp/ical_jsons/gomi.json")) == "gomi"


def test_gomi_event_source_rejects_empty_stem() -> None:
    with pytest.raises(GomiError, match="source を決められません"):
        gomi_event_source(Path("/tmp/ical_jsons/.json"))
