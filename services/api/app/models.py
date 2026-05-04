from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AstrologyCommonParams(BaseModel):
    local_datetime: str | None = None
    utc_datetime: str | None = None
    city: str | None = None
    nation: str | None = None
    lat: float | None = None
    lon: float | None = None
    timezone: str | None = None
    zodiac_type: str | None = None
    houses_system_name: str | None = None
    perspective_type: str | None = None


class AstrologyPoint(BaseModel):
    key: str
    name: str | None = None
    sign: str | None = None
    emoji: str | None = None
    element: str | None = None
    quality: str | None = None
    house: str | None = None
    house_num: int | None = None
    retrograde: bool | None = None
    position: float | None = None


class AstrologyStats(BaseModel):
    element_counts: dict[str, int] = Field(default_factory=dict)
    quality_counts: dict[str, int] = Field(default_factory=dict)
    yin_yang_counts: dict[str, int] = Field(default_factory=dict)


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


class ProfileRequest(BaseModel):
    name: str = "User"
    birth_date: str = Field(..., description="YYYY-MM-DD")
    birth_time: str = Field(..., description="HH:MM")
    birth_city: str
    gender: str | None = None
    domain: str | None = None
    mbti: str | None = None


class TarotCard(BaseModel):

    id: str
    name: str
    arcana: str | None = None
    number: str | None = None
    orientation: Literal["upright", "reversed"]
    meaning_source: Literal["love", "career", "general"]
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
    common_params: AstrologyCommonParams = Field(default_factory=AstrologyCommonParams)
    points: list[AstrologyPoint] = Field(default_factory=list)
    stats: AstrologyStats = Field(default_factory=AstrologyStats)
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


class ProfileResponse(BaseModel):
    schema_version: str = "0.1"
    profile: ReportProfile
    astrology: ReportAstrology
    mbti: ReportMbti | None = None
    action_guide: list[str] = Field(default_factory=list)
    followup_questions: list[str] = Field(default_factory=list)


class TarotDeckRequest(BaseModel):
    question: str
    domain: str | None = None
    spread: SpreadConfig = Field(default_factory=SpreadConfig)


class TarotDeckResponse(BaseModel):
    deck_id: str
    deck_size: int
    required_picks: int


class TarotRevealRequest(BaseModel):
    deck_id: str
    picks: list[int]


class TarotRevealResponse(BaseModel):
    tarot: ReportTarot
    action_guide: list[str] = Field(default_factory=list)
    followup_questions: list[str] = Field(default_factory=list)
