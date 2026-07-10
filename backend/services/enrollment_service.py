"""
Enrollment intelligence data service.
Reads data/processed/features.parquet and calls ML inference wrappers for all
/api/enrollment/* endpoints.
"""
from pathlib import Path
import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent.parent
_PLACEMENTS_CSV = _ROOT / 'data' / 'mock' / 'placements.csv'
_PARQUET = _ROOT / 'data' / 'processed' / 'features.parquet'

_PROGRAMS = [
    'BS Computer Science', 'BS Data Science', 'Certificate Data Analytics',
    'MBA Product Management', 'MS Artificial Intelligence', 'MS Business Analytics',
    'MS Cloud Computing', 'MS Computer Science', 'MS Cybersecurity',
    'MS Data Science', 'MS Human-Computer Interaction', 'MS Information Technology',
]

# SHAP feature name -> human-readable skill label for recommendations
_SHAP_TO_SKILL = {
    'gpa_scaled':                 'Improve academic performance (GPA)',
    'internships':                'Pursue internship opportunities',
    'communication_score_scaled': 'Develop communication skills',
    'projects':                   'Build more portfolio projects',
}

_SKILL_PRIORITY = {
    'gpa_scaled':                 'High',
    'internships':                'High',
    'communication_score_scaled': 'Medium',
    'projects':                   'Medium',
}

_SKILL_REASON = {
    'gpa_scaled':                 'GPA is the top driver of placement probability',
    'internships':                'Industry experience significantly boosts employability',
    'communication_score_scaled': 'Employers rank communication in the top-3 soft skills',
    'projects':                   'Practical projects demonstrate applied competency',
}


# ── Internal helpers ──────────────────────────────────────────────────────────

def _load_parquet() -> pd.DataFrame:
    df = pd.read_parquet(_PARQUET)
    prog_cols = [c for c in df.columns if c.startswith('prog_')]
    df['program'] = df[prog_cols].idxmax(axis=1).str.replace('prog_', '', regex=False)
    return df


def _load_placements() -> pd.DataFrame:
    df = pd.read_csv(_PLACEMENTS_CSV)
    df['placed'] = df['placed'].map(lambda x: str(x).lower() == 'true')
    return df


# ── Public service functions ──────────────────────────────────────────────────

def get_enrollment_summary() -> dict:
    df = _load_parquet()
    placement_rate = round(float(df['placed'].mean()) * 100, 1)
    top_program = (
        df.groupby('program').size().sort_values(ascending=False).index[0]
    )
    by_year = (
        df.groupby('enrollment_year').size()
          .to_dict()
    )
    return {
        'total_students':    int(len(df)),
        'total_programs':    int(df['program'].nunique()),
        'avg_placement_rate': placement_rate,
        'top_program':       top_program,
        'enrollment_by_year': {int(k): int(v) for k, v in by_year.items()},
    }


def get_enrollment_forecast(program: str, n_years: int = 3) -> dict:
    from .ml_service import forecast_enrollment

    df = _load_parquet()

    # Historical counts for the requested program
    hist = (
        df[df['program'] == program]
          .groupby('enrollment_year')
          .size()
          .reset_index(name='count')
          .sort_values('enrollment_year')
    )
    historical = [
        {'year': int(row['enrollment_year']), 'predicted_count': int(row['count'])}
        for _, row in hist.iterrows()
    ]

    # LSTM rolling forecast
    raw = forecast_enrollment(program, n_years=n_years)
    forecast = [
        {'year': p['year'], 'predicted_count': p['predicted_enrollment']}
        for p in raw
    ]

    return {'program': program, 'historical': historical, 'forecast': forecast}


def get_admission_risk(limit: int = 10) -> list:
    df = _load_parquet()

    years = sorted(df['enrollment_year'].unique())
    prev_year, last_year = int(years[-2]), int(years[-1])

    results = []
    for prog in _PROGRAMS:
        prog_df = df[df['program'] == prog]
        count_last = int(len(prog_df[prog_df['enrollment_year'] == last_year]))
        count_prev = int(len(prog_df[prog_df['enrollment_year'] == prev_year]))

        if count_prev == 0:
            continue

        # Positive risk_score = declining enrolment
        pct_change = (count_last - count_prev) / count_prev * 100
        risk_score = round(max(-pct_change, 0.0), 1)   # 0 if growing, >0 if shrinking

        placement_rate = float(prog_df['placed'].mean())
        avg_enroll = (count_prev + count_last) / 2
        recommended_intake = max(10, int(round(avg_enroll * placement_rate)))

        trend = 'up' if pct_change > 2 else ('down' if pct_change < -2 else 'stable')

        results.append({
            'program':            prog,
            'risk_score':         risk_score,
            'recommended_intake': recommended_intake,
            'trend':              trend,
        })

    # Sort by risk descending, return top `limit`
    results.sort(key=lambda r: r['risk_score'], reverse=True)
    return results[:limit]


def get_placement_by_stream() -> list:
    df = _load_parquet()
    placements = _load_placements()

    results = []
    for prog in _PROGRAMS:
        prog_df = df[df['program'] == prog]
        if prog_df.empty:
            continue

        placement_rate = round(float(prog_df['placed'].mean()) * 100, 1)
        student_ids = prog_df['student_id'].tolist()
        placed_rows = placements[
            placements['student_id'].isin(student_ids) & placements['placed']
        ]
        avg_salary = round(float(placed_rows['salary'].mean()), 2) if not placed_rows.empty else 0.0

        results.append({
            'program':        prog,
            'placement_rate': placement_rate,
            'avg_salary':     avg_salary,
            'student_count':  int(len(prog_df)),
        })

    results.sort(key=lambda r: r['placement_rate'], reverse=True)
    return results


def predict_student_placement(student_dict: dict) -> dict:
    from .ml_service import predict_placement, explain_student

    pred = predict_placement(student_dict)
    expl = explain_student(student_dict)

    shap_values = [
        {'feature': c['feature'], 'value': c['value'], 'shap': c['shap']}
        for c in expl['contributions']
    ]

    return {
        'placement_probability': round(pred['placed_probability'], 4),
        'prediction':            pred['predicted_class'],
        'base_value':            expl['base_value'],
        'shap_values':           shap_values,
    }


def get_skill_recommendations(student_id=None) -> dict:
    """
    Rule-based skill recommendations derived from SHAP feature importances.
    If student_id is provided, personalise based on their feature values.
    Otherwise return global recommendations.
    """
    from .ml_service import get_shap_cache

    shap_values, _, feature_names, _ = get_shap_cache()
    feature_names_list = list(feature_names)
    mean_abs = np.abs(shap_values).mean(axis=0)

    # Rank individual skill features by global SHAP importance
    skill_feats = [f for f in feature_names_list if f in _SHAP_TO_SKILL]
    ranked = sorted(
        skill_feats,
        key=lambda f: mean_abs[feature_names_list.index(f)],
        reverse=True,
    )

    recommendations = [
        {
            'skill':    _SHAP_TO_SKILL[feat],
            'priority': _SKILL_PRIORITY[feat],
            'reason':   _SKILL_REASON[feat],
        }
        for feat in ranked
    ]

    pathways = [
        'Consider a Graduate Certificate in Data Science to supplement your degree',
        'Enroll in a part-time MBA to strengthen business communication skills',
        'Pursue cloud certifications (AWS/Azure) to increase hiring appeal',
    ]

    return {
        'student_id':           student_id,
        'recommendations':      recommendations,
        'alternative_pathways': pathways,
    }


_PROGRAM_PATHWAYS = {
    'Certificate Data Analytics':    ['Upgrade to MS Data Science for a 90.7% placement rate', 'Build a data portfolio on GitHub to compensate for the shorter programme', 'Earn an AWS Data Analytics or Google Data Engineer certification'],
    'BS Computer Science':           ['Add a minor in Data Science to broaden ML exposure', 'Target SWE internships at mid-size companies where competition is lower', 'Contribute to open-source projects to build a visible portfolio'],
    'BS Data Science':               ['Consider pursuing MS Data Science after graduation for a salary boost', 'Enrol in a cloud computing elective to add infrastructure skills', 'Secure a research assistantship to gain academic publication experience'],
    'MBA Product Management':        ['Pair the MBA with a technical certification (AWS, PMP, or Six Sigma)', 'Seek cross-functional internships blending product and data roles', 'Build a product case study portfolio showcasing data-driven decisions'],
    'MS Artificial Intelligence':    ['Target AI/ML engineer roles at established tech firms', 'Publish a project on arXiv or Kaggle to differentiate your application', 'Pair AI coursework with cloud ML platform certifications (AWS SageMaker, GCP Vertex)'],
    'MS Business Analytics':         ['Bridge to tech roles by learning Python/SQL if not already proficient', 'Pursue a consulting internship where analytics skills command a premium', 'Earn a Tableau or Power BI certification to stand out in BI roles'],
    'MS Cloud Computing':            ['Target DevOps and cloud architect roles with AWS/Azure/GCP certifications', 'Contribute to infrastructure-as-code projects on GitHub', 'Look for SRE internships — reliability engineering pays a premium'],
    'MS Computer Science':           ['Specialise early in AI, systems, or security to increase focus', 'Complete at least two internships — MS CS placement improves significantly with experience', 'Prepare for technical interviews with LeetCode and system design practice'],
    'MS Cybersecurity':              ['Earn CEH, CISSP, or CompTIA Security+ to signal readiness to employers', 'Look for bug-bounty programmes to build a credible security portfolio', 'Target government or financial sector roles where security pay is highest'],
    'MS Data Science':               ['Pursue research opportunities or Kaggle competitions to strengthen your portfolio', 'Network with alumni in data science roles for referrals', 'Add a cloud ML certification (AWS ML Specialty) to complement the degree'],
    'MS Human-Computer Interaction': ['Target UX researcher roles at tech companies — HCI commands top salaries there', 'Build a design portfolio on Behance or a personal site', 'Supplement with front-end coding skills to bridge design and development'],
    'MS Information Technology':     ['Pursue PMP or ITIL certifications to move into IT management', 'Target project coordinator roles as a stepping stone to IT director positions', 'Develop skills in ERP systems (SAP, Oracle) for enterprise IT roles'],
}

_DEFAULT_PATHWAYS = [
    'Consider a Graduate Certificate in Data Science to supplement your degree',
    'Enroll in a part-time MBA to strengthen business communication skills',
    'Pursue cloud certifications (AWS/Azure) to increase hiring appeal',
]


def get_personalised_skill_roadmap(profile: dict) -> dict:
    """
    Run the placement model once at current profile, then once per feature
    improvement scenario, computing the actual probability gain for each.
    Recommendations are ranked by that data-driven gain.
    """
    from .ml_service import predict_placement as _predict

    current_pred = _predict(profile)
    current_prob = current_pred['placed_probability']

    scenarios = [
        {
            'feature':  'gpa',
            'shap_key': 'gpa_scaled',
            'skill':    'Raise your GPA',
            'target':   min(4.0, round(profile['gpa'] + 0.5, 1)),
            'action':   f'Target GPA {min(4.0, round(profile["gpa"] + 0.5, 1)):.1f} (currently {profile["gpa"]:.1f})',
        },
        {
            'feature':  'internships',
            'shap_key': 'internships',
            'skill':    'Complete an internship',
            'target':   profile['internships'] + 1,
            'action':   f'Secure {profile["internships"] + 1} internship(s) (currently {profile["internships"]})',
        },
        {
            'feature':  'projects',
            'shap_key': 'projects',
            'skill':    'Build portfolio projects',
            'target':   profile['projects'] + 2,
            'action':   f'Complete {profile["projects"] + 2} projects (currently {profile["projects"]})',
        },
        {
            'feature':  'communication_score',
            'shap_key': 'communication_score_scaled',
            'skill':    'Improve communication skills',
            'target':   min(10, profile['communication_score'] + 2),
            'action':   f'Reach score {min(10, profile["communication_score"] + 2)}/10 (currently {profile["communication_score"]}/10)',
        },
    ]

    roadmap = []
    for s in scenarios:
        improved = dict(profile)
        improved[s['feature']] = s['target']
        gain = _predict(improved)['placed_probability'] - current_prob

        if gain >= 0.10:
            priority = 'High'
        elif gain >= 0.04:
            priority = 'Medium'
        else:
            priority = 'Low'

        roadmap.append({
            'skill':             s['skill'],
            'action':            s['action'],
            'priority':          priority,
            'probability_gain':  round(gain * 100, 1),
            'reason':            _SKILL_REASON[s['shap_key']],
        })

    roadmap.sort(key=lambda x: x['probability_gain'], reverse=True)

    pathways = _PROGRAM_PATHWAYS.get(profile.get('program', ''), _DEFAULT_PATHWAYS)

    return {
        'current_probability': round(current_prob * 100, 1),
        'program':             profile.get('program', ''),
        'recommendations':     roadmap,
        'alternative_pathways': pathways,
    }
