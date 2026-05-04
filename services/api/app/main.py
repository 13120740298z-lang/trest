from __future__ import annotations

import hashlib

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .astrology import chart_highlights, compute_chart, parse_birth_info
from .geo import resolve_city
from .models import AnalyzeRequest, AnalyzeResponse
from .report import (
    build_action_guide,
    build_astrology,
    build_followups,
    build_mbti,
    build_profile,
    build_tarot,
)
from .tarot import draw_cards


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
    tarot = build_tarot(spread=req.spread, cards=tarot_cards, domain=req.domain)
    mbti = build_mbti(mbti=req.mbti) if req.mbti else None

    return AnalyzeResponse(
        profile=profile,
        astrology=astrology,
        tarot=tarot,
        mbti=mbti,
        action_guide=build_action_guide(domain=req.domain),
        followup_questions=build_followups(domain=req.domain),
    )
