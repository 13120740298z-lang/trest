from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Literal

from .models import ReportSection, ReportTarot, SpreadConfig, TarotCard


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


def sample_raw_cards(*, seed: int, count: int) -> list[dict[str, Any]]:
    raw_cards = load_cards()
    rng = random.Random(seed)
    if count >= len(raw_cards):
        return list(raw_cards)
    return rng.sample(raw_cards, k=count)


def _count_for_spread(spread_type: str) -> int:
    return 1 if spread_type == "single" else 3


def _build_card(
    *,
    spread: SpreadConfig,
    domain: str | None,
    rng: random.Random,
    raw: dict[str, Any],
) -> TarotCard:
    domain_text = (domain or "").strip().lower()
    use_love = any(k in domain_text for k in ["爱情", "恋爱", "关系", "感情", "love", "relationship"])
    use_career = any(k in domain_text for k in ["事业", "工作", "职业", "career", "job", "work"])
    orientation: Literal["upright", "reversed"] = "upright"
    if spread.include_reversed and rng.random() < 0.4:
        orientation = "reversed"

    keywords = raw.get("upright_keywords") if orientation == "upright" else raw.get("reversed_keywords")

    meaning_source: Literal["love", "career", "general"] = "general"
    meaning = None
    if use_love:
        meaning = raw.get("love_meaning")
        meaning_source = "love"
    elif use_career:
        meaning = raw.get("career_meaning")
        meaning_source = "career"

    if meaning is None or not str(meaning).strip():
        meaning = raw.get("meaning_upright") if orientation == "upright" else raw.get("meaning_reversed")
        meaning_source = "general"
    meaning = str(meaning or "").strip()

    return TarotCard(
        id=raw["id"],
        name=raw["name"],
        arcana=raw.get("arcana"),
        suit=raw.get("suit"),
        number=raw.get("number"),
        orientation=orientation,
        meaning_source=meaning_source,
        keywords=list(keywords or []),
        meaning=meaning,
    )


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
    return [_build_card(spread=spread, domain=domain, rng=rng, raw=c) for c in chosen]


def reveal_cards(
    *,
    spread: SpreadConfig,
    domain: str | None,
    seed: int,
    raws: list[dict[str, Any]],
) -> list[TarotCard]:
    rng = random.Random(seed)
    return [_build_card(spread=spread, domain=domain, rng=rng, raw=c) for c in raws]


def tarot_report(*, spread: SpreadConfig, cards: list[TarotCard]) -> ReportTarot:
    if spread.type == "single":
        title = "单张：当前状态与建议"
    else:
        title = "三张：状态-阻碍-建议"
    joined = "\n".join([f"- {c.name}（{'正位' if c.orientation=='upright' else '逆位'}）：{c.meaning}" for c in cards])
    sections = [
        ReportSection(title=title, content=joined),
        ReportSection(title="落地提醒", content="把牌义当作行动线索而不是命运裁决：用它来做“下一步怎么做更顺”的微调。"),
    ]
    return ReportTarot(spread=spread, cards=cards, interpretation=sections)
