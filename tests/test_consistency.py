"""Phase 5 groundwork — cross-table consistency rules hold on the current data."""
from __future__ import annotations

import pytest

from ml.consistency import RULES, run_rules


def test_every_rule_passes_on_the_published_tables():
    failing = [r for r in run_rules() if r["status"] != "pass"]
    assert failing == [], failing


@pytest.mark.parametrize("rule", RULES, ids=lambda r: r.id)
def test_each_rule_has_a_severity_and_description(rule):
    assert rule.severity in {"critical", "high", "moderate", "low"}
    assert rule.description
