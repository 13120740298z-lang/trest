from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Literal

from .models import SpreadConfig, TarotCard


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _cards_path() -> Path:
    return _repo_root() / "data" / "processed" / "tarot" / "cards.json"


_CARDS_RAW_CACHE: list[dict[str, Any]] | None = None


def load_cards() -> list[dict[str, Any]]:
    global _CARDS_RAW_CACHE
    if _CARDS_RAW_CACHE is not None:
        return _CARDS_RAW_CACHE
    _CARDS_RAW_CACHE = json.loads(_cards_path().read_text(encoding="utf-8"))
    return _CARDS_RAW_CACHE


def _count_for_spread(spread_type: str) -> int:
    return 1 if spread_type == "single" else 3


def draw_cards(
    *,
    spread: SpreadConfig,
    domain: str | None,
    request_seed: int,
) -> list[TarotCard]:
    raw_cards = load_cards()
    n = _count_for_spread(spread.type)
    seed = spread.seed if spread.seed is not None else request_seed
    rng = random.Random(seed)

    chosen = rng.sample(raw_cards, k=min(n, len(raw_cards)))
    out: list[TarotCard] = []
    domain_text = (domain or "").strip().lower()
    use_love = any(k in domain_text for k in ["爱情", "恋爱", "关系", "感情", "love", "relationship"])
    use_career = any(k in domain_text for k in ["事业", "工作", "职业", "career", "job", "work"])
    for c in chosen:
        orientation: Literal["upright", "reversed"] = "upright"
        if spread.include_reversed and rng.random() < 0.4:
            orientation = "reversed"

        keywords = c.get("upright_keywords") if orientation == "upright" else c.get("reversed_keywords")

        meaning_source: Literal["love", "career", "general"] = "general"
        meaning = None
        if use_love:
            meaning = c.get("love_meaning")
            meaning_source = "love"
        elif use_career:
            meaning = c.get("career_meaning")
            meaning_source = "career"

        if meaning is None or not str(meaning).strip():
            meaning = c.get("meaning_upright") if orientation == "upright" else c.get("meaning_reversed")
            meaning_source = "general"
        meaning = str(meaning or "").strip()

        out.append(
            TarotCard(
                id=c["id"],
                name=c["name"],
                arcana=c.get("arcana"),
                suit=c.get("suit"),
                number=c.get("number"),
                orientation=orientation,
                meaning_source=meaning_source,
                keywords=list(keywords or []),
                meaning=meaning,
            )
        )
    return out
