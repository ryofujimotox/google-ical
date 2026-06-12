"""ゴミ収集日設定 JSON の読込。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

from google_ical.constants import DEFAULT_GOMI_OUTPUT
from google_ical.exceptions import GomiError


class _GomiSectionSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    region: str
    output_file: str = DEFAULT_GOMI_OUTPUT
    pdf_url_override: str | None = None


class _GomiConfigSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gomi: _GomiSectionSchema


@dataclass(frozen=True)
class GomiConfig:
    """fetch_gomi が使うゴミ収集日設定。"""

    region: str
    output_file: str
    pdf_url_override: str | None


def load_gomi_config(path: Path) -> GomiConfig:
    if not path.is_file():
        raise GomiError(f"ゴミ収集日設定ファイルがありません: {path}")

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        parsed = _GomiConfigSchema.model_validate(raw)
    except json.JSONDecodeError as exc:
        raise GomiError(f"ゴミ収集日設定 JSON の解析に失敗しました: {path}") from exc
    except ValidationError as exc:
        raise GomiError(f"ゴミ収集日設定 JSON の形式が不正です: {path}") from exc

    return GomiConfig(
        region=parsed.gomi.region,
        output_file=parsed.gomi.output_file,
        pdf_url_override=parsed.gomi.pdf_url_override,
    )
