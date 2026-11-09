"""SCOPE.STU cell-size gate.

The live function lives in backend/services/auth_service.py. Host pytest does
not install python-jose, so this file asserts the constant in source rather
than importing FastAPI.
"""
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "backend" / "services" / "auth_service.py"
STUDENT = Path(__file__).resolve().parents[1] / "backend" / "services" / "student_service.py"


def test_min_cell_size_is_five():
    text = SRC.read_text(encoding="utf-8")
    assert "MIN_CELL_SIZE = 5" in text
    assert "def cell_released" in text
    assert "int(n) >= MIN_CELL_SIZE" in text


def test_labour_outlook_withholds_small_cells():
    """The minimum cell size applies to each occupation row's own count. The
    earlier rule compared the number of occupation categories (always one per
    field) with the threshold, so W.STU.02 could never render."""
    text = STUDENT.read_text(encoding="utf-8")
    assert "cell_withheld" in text
    assert "min_cell_size" in text
    assert 'cell_released(o["vacancies"])' in text
    assert "cell_released(n_occ)" not in text
