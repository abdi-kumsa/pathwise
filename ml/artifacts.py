"""
Verified access to model artefacts (plan item 3.8).

Every pickle / Keras load goes through `verified_open` or `verify`, which
compares the file's SHA-256 with ml/models/MANIFEST.sha256.json and raises
`ArtifactIntegrityError` on a mismatch or an unlisted file. `pickle.load`
executes code from the file, so an unverified artefact is not loaded at all.

Regenerate the manifest after a retrain: python scripts/artifact_manifest.py
"""
from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

MODELS = Path(__file__).resolve().parent / "models"
MANIFEST = MODELS / "MANIFEST.sha256.json"


class ArtifactIntegrityError(RuntimeError):
    """An artefact is missing from the manifest or its hash does not match."""


@lru_cache(maxsize=1)
def _manifest() -> dict:
    if not MANIFEST.exists():
        raise ArtifactIntegrityError(
            f"{MANIFEST} is missing. Run python scripts/artifact_manifest.py.")
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(path) -> Path:
    path = Path(path).resolve()
    expected = _manifest().get(path.name)
    if expected is None:
        raise ArtifactIntegrityError(f"{path.name} is not in the artefact manifest; refusing to load it.")
    actual = _sha256(path)
    if actual != expected:
        raise ArtifactIntegrityError(
            f"{path.name} does not match its recorded SHA-256; refusing to load it. "
            "If this is a deliberate retrain, run python scripts/artifact_manifest.py.")
    return path


def verified_open(path):
    """open(path, 'rb') after the integrity check."""
    return open(verify(path), "rb")


def reset_cache() -> None:
    _manifest.cache_clear()
