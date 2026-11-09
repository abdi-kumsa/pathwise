"""
SHA-256 manifest for the model artefacts in ml/models/ (plan item 3.8).

`pickle.load` executes code from the file it reads, so a swapped .pkl is a
code-execution path at startup. backend/services/ml_service.py verifies each
artefact against this manifest and refuses to load one that does not match.

    python scripts/artifact_manifest.py            # regenerate after a retrain
    python scripts/artifact_manifest.py --check    # exit 1 on any mismatch
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

MODELS = Path(__file__).resolve().parents[1] / "ml" / "models"
MANIFEST = MODELS / "MANIFEST.sha256.json"
PATTERNS = ("*.pkl", "*.keras", "*.joblib")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build() -> dict:
    files = sorted(p for pat in PATTERNS for p in MODELS.glob(pat))
    return {p.name: sha256(p) for p in files}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    current = build()
    if args.check:
        recorded = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
        bad = sorted(set(current) ^ set(recorded) | {k for k in current if recorded.get(k) != current[k]})
        for name in bad:
            print(f"mismatch: {name}", file=sys.stderr)
        return 1 if bad else 0
    MANIFEST.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(current)} hashes to {MANIFEST.relative_to(MODELS.parents[1])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
