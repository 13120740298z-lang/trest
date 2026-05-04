from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path


DATASET_SLUG = "morrispoint/complete-tarot-card-meanings-all-78-cards"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def download_kaggle_tarot(*, raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "kaggle",
            "datasets",
            "download",
            DATASET_SLUG,
            "-p",
            str(raw_dir),
            "--unzip",
        ],
        check=True,
    )


def download_kagglehub_tarot(*, raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    import kagglehub

    kagglehub.dataset_download(DATASET_SLUG, output_dir=str(raw_dir))


def _first_existing(path: Path, candidates: list[str]) -> Path:
    for name in candidates:
        p = path / name
        if p.exists():
            return p
    raise FileNotFoundError(str(path))


def _slugify(value: str) -> str:
    out: list[str] = []
    prev_underscore = False
    for ch in value.lower():
        if ch.isalnum():
            out.append(ch)
            prev_underscore = False
        else:
            if not prev_underscore:
                out.append("_")
                prev_underscore = True
    return "".join(out).strip("_")


def _split_keywords(value: str) -> list[str]:
    return [x.strip() for x in str(value).split(",") if x and str(x).strip()]


def parse_tarot_cards(*, raw_dir: Path, out_file: Path) -> None:
    csv_path = _first_existing(
        raw_dir,
        [
            "tarot.csv",
            "tarot_card_meanings.csv",
            "tarot_card_meanings_all_78_cards.csv",
            "complete-tarot-card-meanings.csv",
            "complete_tarot_card_meanings.csv",
        ],
    )

    cards: list[dict] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("card_name") or row.get("name") or row.get("Name") or "").strip()
            if not name:
                continue

            arcana_raw = (row.get("arcana") or row.get("Arcana") or "").strip()
            suit_raw = row.get("suit") or row.get("Suit") or ""
            suit = None
            if suit_raw and str(suit_raw).strip() and str(suit_raw).lower() != "nan":
                suit = str(suit_raw).strip().lower()

            num_raw = row.get("card_number") or row.get("number") or row.get("Number")
            number: str | None = None
            if num_raw is not None and str(num_raw).strip() and str(num_raw).lower() != "nan":
                try:
                    number = str(int(float(str(num_raw).strip())))
                except ValueError:
                    number = str(num_raw).strip()

            arcana = arcana_raw.lower() if arcana_raw else None

            card_id = (row.get("id") or row.get("Id") or "").strip()
            if not card_id:
                slug = _slugify(name)
                if arcana == "major":
                    card_id = f"major_{(number or 'x').zfill(2)}_{slug}"
                else:
                    card_id = f"minor_{(suit or 'unknown')}_{number or 'x'}_{slug}"

            meaning_u = (
                row.get("upright_meaning")
                or row.get("meaning_upright")
                or row.get("Meaning Upright")
                or row.get("upright")
                or ""
            )
            meaning_r = (
                row.get("reversed_meaning")
                or row.get("meaning_reversed")
                or row.get("Meaning Reversed")
                or row.get("reversed")
                or ""
            )
            meaning_u = str(meaning_u).strip()
            meaning_r = str(meaning_r).strip()

            upr_kw = row.get("upright_keywords") or row.get("Upright Keywords") or meaning_u
            rev_kw = row.get("reversed_keywords") or row.get("Reversed Keywords") or meaning_r

            love = row.get("love_meaning") or row.get("Love Meaning") or ""
            career = row.get("career_meaning") or row.get("Career Meaning") or ""

            cards.append(
                {
                    "id": card_id,
                    "name": name,
                    "arcana": arcana,
                    "suit": suit,
                    "number": number,
                    "upright_keywords": _split_keywords(str(upr_kw)),
                    "reversed_keywords": _split_keywords(str(rev_kw)),
                    "meaning_upright": meaning_u,
                    "meaning_reversed": meaning_r,
                    "love_meaning": str(love).strip() if str(love).strip() and str(love).lower() != "nan" else "",
                    "career_meaning": str(career).strip()
                    if str(career).strip() and str(career).lower() != "nan"
                    else "",
                }
            )

    if len(cards) != 78:
        raise RuntimeError(f"expected_78_cards_got:{len(cards)}")
    names = [c["name"] for c in cards]
    if len(set(names)) != len(names):
        raise RuntimeError("duplicate_card_name")

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--download-method", default="auto", choices=["auto", "kagglehub", "kaggle"])
    parser.add_argument("--raw-dir", default=str(_repo_root() / "data" / "raw" / "kaggle" / "tarot"))
    parser.add_argument("--out", default=str(_repo_root() / "data" / "processed" / "tarot" / "cards.json"))
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    out_file = Path(args.out)

    if args.download:
        if args.download_method in ("auto", "kagglehub"):
            try:
                download_kagglehub_tarot(raw_dir=raw_dir)
            except Exception:
                if args.download_method == "kagglehub":
                    raise
                download_kaggle_tarot(raw_dir=raw_dir)
        else:
            download_kaggle_tarot(raw_dir=raw_dir)
    parse_tarot_cards(raw_dir=raw_dir, out_file=out_file)


if __name__ == "__main__":
    main()
