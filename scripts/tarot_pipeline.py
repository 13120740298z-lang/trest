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


def _first_existing(path: Path, candidates: list[str]) -> Path:
    for name in candidates:
        p = path / name
        if p.exists():
            return p
    raise FileNotFoundError(str(path))


def parse_tarot_cards(*, raw_dir: Path, out_file: Path) -> None:
    csv_path = _first_existing(
        raw_dir,
        [
            "tarot.csv",
            "tarot_card_meanings.csv",
            "complete-tarot-card-meanings.csv",
            "complete_tarot_card_meanings.csv",
        ],
    )

    cards: list[dict] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("name") or row.get("Name") or "").strip()
            if not name:
                continue

            card_id = (row.get("id") or row.get("Id") or "").strip()
            if not card_id:
                card_id = name.lower().replace(" ", "_").replace("-", "_")

            meaning_u = (row.get("meaning_upright") or row.get("Meaning Upright") or row.get("upright") or "").strip()
            meaning_r = (row.get("meaning_reversed") or row.get("Meaning Reversed") or row.get("reversed") or "").strip()

            upr_kw = row.get("upright_keywords") or row.get("Upright Keywords") or ""
            rev_kw = row.get("reversed_keywords") or row.get("Reversed Keywords") or ""

            cards.append(
                {
                    "id": card_id,
                    "name": name,
                    "arcana": (row.get("arcana") or row.get("Arcana") or None),
                    "suit": (row.get("suit") or row.get("Suit") or None),
                    "number": (row.get("number") or row.get("Number") or None),
                    "upright_keywords": [x.strip() for x in str(upr_kw).split(",") if x.strip()],
                    "reversed_keywords": [x.strip() for x in str(rev_kw).split(",") if x.strip()],
                    "meaning_upright": meaning_u,
                    "meaning_reversed": meaning_r,
                }
            )

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--raw-dir", default=str(_repo_root() / "data" / "raw" / "kaggle" / "tarot"))
    parser.add_argument("--out", default=str(_repo_root() / "data" / "processed" / "tarot" / "cards.json"))
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    out_file = Path(args.out)

    if args.download:
        download_kaggle_tarot(raw_dir=raw_dir)
    parse_tarot_cards(raw_dir=raw_dir, out_file=out_file)


if __name__ == "__main__":
    main()

