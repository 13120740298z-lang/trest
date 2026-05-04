from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class SpreadConfig(BaseModel):
    type: Literal["single", "three"] = "single"
    include_reversed: bool = True
    seed: int | None = None


class AnalyzeRequest(BaseModel):
    name: str = "User"
    birth_date: str = Field(..., description="YYYY-MM-DD")
    birth_time: str = Field(..., description="HH:MM")
    birth_city: str
    gender: str | None = None
    domain: str | None = None
    mbti: str | None = None
    spread: SpreadConfig = Field(default_factory=SpreadConfig)


class TarotCard(BaseModel):
    id: str
    name: str
    arcana: str | None = None
    suit: str | None = None
    number: str | None = None
    orientation: Literal["upright", "reversed"]
    keywords: list[str] = Field(default_factory=list)
    meaning: str


class ReportSection(BaseModel):
    title: str
    content: str


class ReportProfile(BaseModel):
    summary: str
    traits: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    blind_spots: list[str] = Field(default_factory=list)


class ReportAstrology(BaseModel):
    raw_chart: dict[str, Any]
    highlights: list[str] = Field(default_factory=list)
    interpretation: list[ReportSection] = Field(default_factory=list)


class ReportTarot(BaseModel):
    spread: SpreadConfig
    cards: list[TarotCard] = Field(default_factory=list)
    interpretation: list[ReportSection] = Field(default_factory=list)


class ReportMbti(BaseModel):
    type: str
    interpretation: list[ReportSection] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    schema_version: str = "0.1"
    profile: ReportProfile
    astrology: ReportAstrology
    tarot: ReportTarot
    mbti: ReportMbti | None = None
    action_guide: list[str] = Field(default_factory=list)
    followup_questions: list[str] = Field(default_factory=list)

