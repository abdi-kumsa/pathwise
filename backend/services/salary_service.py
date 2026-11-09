"""
Salary forecasting data service.
Reads data/processed/features.parquet and calls the salary ML inference
wrapper for all /api/recommendations/salary-* endpoints.
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


def _program_avg_salary(df: pd.DataFrame, program: str) -> float:
    """Average salary for placed students in a given program."""
    placed = df[(df['program'] == program) & (df['placed'] == 1)]
    sal = placed['salary'].dropna()
    return round(float(sal.mean()), 2) if not sal.empty else 0.0


# ── Public service functions ──────────────────────────────────────────────────

def get_program_salary_breakdown() -> dict:
    df = _load_parquet()
    placed_df = df[df['placed'] == 1].dropna(subset=['salary'])

    programs_out = []
    for prog in _PROGRAMS:
        all_prog   = df[df['program'] == prog]
        placed_prog = placed_df[placed_df['program'] == prog]

        if all_prog.empty:
            continue

        avg_salary    = round(float(placed_prog['salary'].mean()),   2) if not placed_prog.empty else 0.0
        median_salary = round(float(placed_prog['salary'].median()), 2) if not placed_prog.empty else 0.0
        placement_rate = round(float(all_prog['placed'].mean()) * 100, 1)
        student_count  = int(len(all_prog))

        programs_out.append({
            'program':        prog,
            'avg_salary':     avg_salary,
            'median_salary':  median_salary,
            'placement_rate': placement_rate,
            'student_count':  student_count,
        })

    programs_out.sort(key=lambda r: r['avg_salary'], reverse=True)

    overall_avg = round(float(placed_df['salary'].mean()), 2) if not placed_df.empty else 0.0
    top_program = programs_out[0]['program'] if programs_out else ''

    return {
        'programs':         programs_out,
        'overall_avg_salary': overall_avg,
        'top_program':      top_program,
    }


def predict_student_salary(profile_dict: dict) -> dict:
    from .ml_service import predict_salary

    result = predict_salary(profile_dict)

    # Attach the program average for comparison
    df = _load_parquet()
    prog_avg = _program_avg_salary(df, profile_dict.get('program', ''))

    return {
        'predicted_salary':   result['predicted_salary'],
        'confidence_low':     result['confidence_low'],
        'confidence_high':    result['confidence_high'],
        'program_avg_salary': prog_avg,
    }
