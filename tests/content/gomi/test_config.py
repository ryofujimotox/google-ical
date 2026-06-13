"""content/gomi/config.py の単体テスト。"""

from __future__ import annotations

import pytest

from google_ical.content.gomi.config import resolve_gomi_output_path
from google_ical.exceptions import GomiError


def test_resolve_gomi_output_path_accepts_filename_in_events_dir(tmp_path) -> None:
    events_dir = tmp_path / "events"
    events_dir.mkdir()

    resolved = resolve_gomi_output_path(events_dir, "gomi.json")

    assert resolved == events_dir / "gomi.json"


@pytest.mark.parametrize("output_file", ("/tmp/gomi.json", "../outside.json", "nested/gomi.json"))
def test_resolve_gomi_output_path_rejects_escape(tmp_path, output_file: str) -> None:
    events_dir = tmp_path / "events"
    events_dir.mkdir()

    with pytest.raises(GomiError, match="output_file"):
        resolve_gomi_output_path(events_dir, output_file)


@pytest.mark.parametrize("output_file", ("gomi.txt", "gomi", "gomi.JSON"))
def test_resolve_gomi_output_path_rejects_non_json_filename(tmp_path, output_file: str) -> None:
    events_dir = tmp_path / "events"
    events_dir.mkdir()

    with pytest.raises(GomiError, match=".json"):
        resolve_gomi_output_path(events_dir, output_file)
