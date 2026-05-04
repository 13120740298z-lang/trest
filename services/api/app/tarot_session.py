from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TarotDeck:
    created_at: float
    raw_cards: list[dict[str, Any]]
    domain: str | None
    include_reversed: bool
    spread_type: str
    seed: int


_DECKS: dict[str, TarotDeck] = {}


def create_deck(*, raw_cards: list[dict[str, Any]], domain: str | None, spread_type: str, include_reversed: bool, seed: int) -> str:
    deck_id = secrets.token_urlsafe(16)
    _DECKS[deck_id] = TarotDeck(
        created_at=time.time(),
        raw_cards=raw_cards,
        domain=domain,
        include_reversed=include_reversed,
        spread_type=spread_type,
        seed=seed,
    )
    return deck_id


def get_deck(deck_id: str) -> TarotDeck | None:
    return _DECKS.get(deck_id)


def delete_deck(deck_id: str) -> None:
    _DECKS.pop(deck_id, None)

