from __future__ import annotations

import argparse
import json
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _src_dir() -> Path:
    return _repo_root() / "third_party" / "Machine-Mindset" / "datasets" / "behaviour" / "zh"


def _clean_example(text: str) -> str:
    t = " ".join(text.strip().split())
    if len(t) > 140:
        t = t[:140].rstrip() + "…"
    return t


def _examples_from_file(path: Path, *, limit: int) -> list[str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        s = _clean_example(str(item.get("output") or ""))
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
        if len(out) >= limit:
            break
    return out


def build_assets(*, src_dir: Path, out_path: Path, limit_per_side: int) -> None:
    mapping: dict[str, dict] = {
        "E": {"file": "zh_energy_extraversion.json", "label": "外向(E)"},
        "I": {"file": "zh_energy_introversion.json", "label": "内向(I)"},
        "S": {"file": "zh_information_sensing.json", "label": "感知(S)"},
        "N": {"file": "zh_information_intuition.json", "label": "直觉(N)"},
        "T": {"file": "zh_decision_thinking.json", "label": "思维(T)"},
        "F": {"file": "zh_decision_feeling.json", "label": "感觉(F)"},
        "J": {"file": "zh_execution_judging.json", "label": "判断(J)"},
        "P": {"file": "zh_execution_perceiving.json", "label": "感知(P)"},
    }

    sides: dict[str, dict] = {}
    for code, meta in mapping.items():
        fp = src_dir / meta["file"]
        examples = _examples_from_file(fp, limit=limit_per_side)
        sides[code] = {"label": meta["label"], "examples": examples}

    out = {
        "language": "zh",
        "source": {
            "repo": "PKU-YuanGroup/Machine-Mindset",
            "path": "datasets/behaviour/zh/*.json",
        },
        "sides": sides,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", default=str(_src_dir()))
    parser.add_argument("--out", default=str(_repo_root() / "data" / "processed" / "mbti" / "behaviour_zh.json"))
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    build_assets(src_dir=Path(args.src), out_path=Path(args.out), limit_per_side=int(args.limit))


if __name__ == "__main__":
    main()

