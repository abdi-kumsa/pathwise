"""Plan item 3.8 — model artefacts are verified before they are deserialised."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from ml import artifacts


@pytest.fixture
def scratch():
    """A private temporary directory (independent of pytest's shared tmp root)."""
    with tempfile.TemporaryDirectory(prefix="pw-artifacts-") as d:
        yield Path(d)


def test_manifest_matches_every_artefact_on_disk():
    import subprocess
    import sys
    r = subprocess.run([sys.executable, "scripts/artifact_manifest.py", "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_a_tampered_artefact_is_refused(scratch):
    original = artifacts.MODELS / "salary_xgboost_meta.pkl"
    copy = scratch / original.name
    shutil.copy(original, copy)
    with copy.open("ab") as fh:
        fh.write(b"tampered")
    with pytest.raises(artifacts.ArtifactIntegrityError):
        artifacts.verify(copy)


def test_an_unlisted_artefact_is_refused(scratch):
    stray = scratch / "not_in_manifest.pkl"
    stray.write_bytes(b"\x80\x04N.")
    with pytest.raises(artifacts.ArtifactIntegrityError):
        artifacts.verify(stray)


def test_no_loader_bypasses_the_check():
    """Every artefact open in the loaders goes through verified_open."""
    import re
    files = [*Path("ml").glob("*.py"), Path("backend/services/ml_service.py")]
    raw = re.compile(r"open\([^)\n]*['\"]rb['\"]\)")
    offenders = [str(p) for p in files
                 if p.name not in {"artifacts.py"} and raw.search(p.read_text(encoding="utf-8"))]
    assert offenders == [], offenders
