from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MbtiSide:
    code: str
    label: str
    examples: list[str]


@dataclass(frozen=True)
class MbtiAssets:
    language: str
    sides: dict[str, MbtiSide]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _assets_path() -> Path:
    return _repo_root() / "data" / "processed" / "mbti" / "behaviour_zh.json"


_CACHE: MbtiAssets | None = None


def load_mbti_assets() -> MbtiAssets:
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    p = _assets_path()
    raw = json.loads(p.read_text(encoding="utf-8"))
    sides: dict[str, MbtiSide] = {}
    for code, v in raw["sides"].items():
        sides[code.upper()] = MbtiSide(code=code.upper(), label=v["label"], examples=list(v.get("examples", [])))

    _CACHE = MbtiAssets(language=raw.get("language", "zh"), sides=sides)
    return _CACHE

