from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class City:
    name: str
    name_en: str
    country: str
    lat: float
    lon: float
    timezone: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _cities_path() -> Path:
    return _repo_root() / "data" / "processed" / "geo" / "cities.json"


_CITIES_CACHE: list[City] | None = None


def load_cities() -> list[City]:
    global _CITIES_CACHE
    if _CITIES_CACHE is not None:
        return _CITIES_CACHE

    raw = json.loads(_cities_path().read_text(encoding="utf-8"))
    _CITIES_CACHE = [
        City(
            name=item["name"],
            name_en=item["name_en"],
            country=item.get("country", ""),
            lat=float(item["lat"]),
            lon=float(item["lon"]),
            timezone=item["timezone"],
        )
        for item in raw
    ]
    return _CITIES_CACHE


def resolve_city(query: str) -> City:
    q = query.strip()
    q_lower = q.lower()
    for city in load_cities():
        if q == city.name or q_lower == city.name_en.lower():
            return city
    raise ValueError(f"city_not_found:{query}")
