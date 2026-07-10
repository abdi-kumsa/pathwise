"""
Escape route mapping service.
Reuses the XGBoost placement model to simulate a student across all 12
programmes and return ranked alternatives with better placement outcomes.
No new model required — pure inference reuse.
"""
from pathlib import Path
import pandas as pd

_ROOT    = Path(__file__).resolve().parent.parent.parent
_PARQUET = _ROOT / 'data' / 'processed' / 'features.parquet'

_PROGRAMS = [
    'BS Computer Science', 'BS Data Science', 'Certificate Data Analytics',
    'MBA Product Management', 'MS Artificial Intelligence', 'MS Business Analytics',
    'MS Cloud Computing', 'MS Computer Science', 'MS Cybersecurity',
    'MS Data Science', 'MS Human-Computer Interaction', 'MS Information Technology',
]


def _load_parquet() -> pd.DataFrame:
    df = pd.read_parquet(_PARQUET)
    prog_cols = [c for c in df.columns if c.startswith('prog_')]
    df['program'] = df[prog_cols].idxmax(axis=1).str.replace('prog_', '', regex=False)
    return df


def _prog_stats(df: pd.DataFrame) -> dict:
    """Compute avg_salary and placement_rate for each program from parquet."""
    stats = {}
    for prog in _PROGRAMS:
        prog_df   = df[df['program'] == prog]
        placed_df = prog_df[prog_df['placed'] == 1]
        sal = placed_df['salary'].dropna()
        stats[prog] = {
            'avg_salary':     round(float(sal.mean()), 2) if not sal.empty else 0.0,
            'placement_rate': round(float(prog_df['placed'].mean()) * 100, 1) if not prog_df.empty else 0.0,
        }
    return stats


def _build_rationale(prob: float, current_prob: float,
                     avg_salary: float, current_salary: float) -> str:
    parts = []

    prob_gain = prob - current_prob
    if prob_gain >= 0.15:
        parts.append(f"+{prob_gain:.0%} placement probability gain")
    elif prob_gain > 0:
        parts.append(f"+{prob_gain:.0%} placement probability")

    if current_salary > 0 and avg_salary > current_salary:
        diff = avg_salary - current_salary
        parts.append(f"${diff:,.0f} higher avg salary")
    elif avg_salary > 0 and current_salary == 0:
        parts.append(f"${avg_salary:,.0f} avg salary for placed graduates")

    if prob >= 0.85:
        parts.append("strong placement match for your profile")
    elif prob >= 0.70:
        parts.append("solid placement match")

    return ". ".join(parts).capitalize() if parts else "Alternative pathway with comparable outcomes"


# ── Public service functions ──────────────────────────────────────────────────

def get_escape_routes(profile_dict: dict, top_n: int = 5) -> dict:
    """
    Simulate the student across all 12 programs using the existing XGBoost
    placement model. Return the top_n programs (excluding their current one)
    ranked by predicted placement probability.
    """
    from .ml_service import predict_placement

    current_prog = profile_dict['program']

    # Current placement probability
    current_result   = predict_placement(profile_dict)
    current_prob     = current_result['placed_probability']

    df    = _load_parquet()
    stats = _prog_stats(df)
    current_salary = stats.get(current_prog, {}).get('avg_salary', 0.0)

    routes = []
    for prog in _PROGRAMS:
        if prog == current_prog:
            continue

        alt_profile = {**profile_dict, 'program': prog}
        result      = predict_placement(alt_profile)
        prob        = result['placed_probability']
        s           = stats[prog]

        routes.append({
            'program':               prog,
            'placement_probability': round(prob, 4),
            'avg_salary':            s['avg_salary'],
            'placement_rate':        s['placement_rate'],
            'rationale':             _build_rationale(prob, current_prob,
                                                      s['avg_salary'], current_salary),
        })

    routes.sort(key=lambda r: r['placement_probability'], reverse=True)
    top = routes[:top_n]

    return {
        'current_program':     current_prog,
        'current_probability': round(current_prob, 4),
        'routes':              top,
    }


def get_program_escape_routes(program_name: str, top_n: int = 5) -> dict:
    """
    Build an escape route map for the median student profile in a given
    programme. Useful for advisory/aggregate views without a specific student.
    """
    df = _load_parquet()
    prog_df = df[df['program'] == program_name]

    if prog_df.empty:
        raise ValueError(f"Program '{program_name}' not found")

    # Median profile for the program (round to nearest int for discrete fields)
    median_profile = {
        'gpa':                 round(float(prog_df['gpa'].median()), 2),
        'internships':         int(round(prog_df['internships'].median())),
        'projects':            int(round(prog_df['projects'].median())),
        'communication_score': int(round(prog_df['communication_score'].median())),
        'program':             program_name,
    }

    return get_escape_routes(median_profile, top_n=top_n)
