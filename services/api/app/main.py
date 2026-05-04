from __future__ import annotations

import hashlib

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .astrology import chart_highlights, compute_chart, parse_birth_info
from .geo import resolve_city
from .models import (
    AnalyzeRequest,
    AnalyzeResponse,
    ProfileRequest,
    ProfileResponse,
    TarotDeckRequest,
    TarotDeckResponse,
    TarotRevealRequest,
    TarotRevealResponse,
)
from .report import (
    build_action_guide,
    build_astrology,
    build_followups,
    build_mbti,
    build_profile,
)
from .tarot import draw_cards, reveal_cards, tarot_report
from .tarot_session import create_deck, delete_deck, get_deck
from .tarot import sample_raw_cards
from .models import SpreadConfig


app = FastAPI(title="Personality MVP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    try:
        city = resolve_city(req.birth_city)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    birth = parse_birth_info(
        name=req.name,
        birth_date=req.birth_date,
        birth_time=req.birth_time,
        city=city,
    )
    chart = compute_chart(birth)
    highlights = chart_highlights(chart)

    seed_bytes = f"{req.birth_date}|{req.birth_time}|{req.birth_city}|{req.domain or ''}".encode("utf-8")
    request_seed = int(hashlib.sha256(seed_bytes).hexdigest()[:8], 16)
    tarot_cards = draw_cards(spread=req.spread, domain=req.domain, request_seed=request_seed)

    profile = build_profile(chart=chart, mbti=req.mbti)
    astrology = build_astrology(chart=chart, highlights=highlights)
    tarot = tarot_report(spread=req.spread, cards=tarot_cards)
    mbti = build_mbti(mbti=req.mbti) if req.mbti else None

    return AnalyzeResponse(
        profile=profile,
        astrology=astrology,
        tarot=tarot,
        mbti=mbti,
        action_guide=build_action_guide(domain=req.domain),
        followup_questions=build_followups(domain=req.domain),
    )


@app.post("/api/profile", response_model=ProfileResponse)
def profile(req: ProfileRequest) -> ProfileResponse:
    try:
        city = resolve_city(req.birth_city)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    birth = parse_birth_info(
        name=req.name,
        birth_date=req.birth_date,
        birth_time=req.birth_time,
        city=city,
    )
    chart = compute_chart(birth)
    highlights = chart_highlights(chart)

    profile = build_profile(chart=chart, mbti=req.mbti)
    astrology = build_astrology(chart=chart, highlights=highlights)
    mbti = build_mbti(mbti=req.mbti) if req.mbti else None

    return ProfileResponse(
        profile=profile,
        astrology=astrology,
        mbti=mbti,
        action_guide=build_action_guide(domain=req.domain),
        followup_questions=build_followups(domain=req.domain),
    )


@app.post("/api/tarot/deck", response_model=TarotDeckResponse)
def tarot_deck(req: TarotDeckRequest) -> TarotDeckResponse:
    seed_bytes = f"{req.question}|{req.domain or ''}|{req.spread.type}|{req.spread.include_reversed}".encode("utf-8")
    seed = int(hashlib.sha256(seed_bytes).hexdigest()[:8], 16)

    deck_size = 12
    required_picks = 1 if req.spread.type == "single" else 3

    deck_raw = sample_raw_cards(seed=seed, count=deck_size)
    deck_size = len(deck_raw)

    deck_id = create_deck(
        raw_cards=deck_raw,
        domain=req.domain,
        spread_type=req.spread.type,
        include_reversed=req.spread.include_reversed,
        seed=seed,
    )
    return TarotDeckResponse(deck_id=deck_id, deck_size=deck_size, required_picks=required_picks)


@app.post("/api/tarot/reveal", response_model=TarotRevealResponse)
def tarot_reveal(req: TarotRevealRequest) -> TarotRevealResponse:
    deck = get_deck(req.deck_id)
    if deck is None:
        raise HTTPException(status_code=400, detail="deck_not_found")

    required = 1 if deck.spread_type == "single" else 3
    if len(req.picks) != required:
        raise HTTPException(status_code=400, detail="invalid_picks")

    if any((p < 0 or p >= len(deck.raw_cards)) for p in req.picks):
        raise HTTPException(status_code=400, detail="pick_out_of_range")

    raws = [deck.raw_cards[i] for i in req.picks]
    spread = SpreadConfig(type=deck.spread_type, include_reversed=deck.include_reversed, seed=None)
    cards = reveal_cards(spread=spread, domain=deck.domain, seed=deck.seed, raws=raws)
    report = tarot_report(spread=spread, cards=cards)

    delete_deck(req.deck_id)

    return TarotRevealResponse(
        tarot=report,
        action_guide=build_action_guide(domain=deck.domain),
        followup_questions=build_followups(domain=deck.domain),
    )
