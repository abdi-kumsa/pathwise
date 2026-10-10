"""Model 3 — education–employment alignment and recommendation engine."""
from .gap import alignment_score, supply_demand_gap
from .pathways import pathway_graph
from .recommend import institution_actions, policy_priority, student_alternatives
from .scenario import run_scenario
from .supply import graduate_supply

__all__ = [
    "graduate_supply",
    "supply_demand_gap",
    "alignment_score",
    "student_alternatives",
    "institution_actions",
    "policy_priority",
    "pathway_graph",
    "run_scenario",
]
