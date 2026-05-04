from __future__ import annotations

from dataclasses import dataclass

from kerykeion import AstrologicalSubject

from .geo import City


@dataclass(frozen=True)
class BirthInfo:
    name: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    city: City


def parse_birth_info(*, name: str, birth_date: str, birth_time: str, city: City) -> BirthInfo:
    y, m, d = (int(x) for x in birth_date.split("-"))
    hh, mm = (int(x) for x in birth_time.split(":"))
    return BirthInfo(
        name=name,
        year=y,
        month=m,
        day=d,
        hour=hh,
        minute=mm,
        city=city,
    )


def compute_chart(birth: BirthInfo) -> dict:
    subject = AstrologicalSubject(
        name=birth.name,
        year=birth.year,
        month=birth.month,
        day=birth.day,
        hour=birth.hour,
        minute=birth.minute,
        lng=birth.city.lon,
        lat=birth.city.lat,
        tz_str=birth.city.timezone,
        city=birth.city.name_en,
        nation=birth.city.country or None,
        online=False,
    )
    return subject.model_dump()


def chart_highlights(chart: dict) -> list[str]:
    sun = chart.get("sun", {})
    moon = chart.get("moon", {})
    asc = chart.get("ascendant", {})
    out: list[str] = []
    if sun.get("sign"):
        out.append(f"太阳：{sun.get('sign')} {sun.get('emoji', '')}".strip())
    if moon.get("sign"):
        out.append(f"月亮：{moon.get('sign')} {moon.get('emoji', '')}".strip())
    if asc.get("sign"):
        out.append(f"上升：{asc.get('sign')} {asc.get('emoji', '')}".strip())
    return out
