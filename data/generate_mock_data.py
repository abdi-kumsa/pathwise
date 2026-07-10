"""
Phase 2 — Step 1
Generates students.csv and placements.csv into data/mock/.

students : 3,000 rows  — Faker names + constrained random values
placements: one row per student — derived using per-program employment
            rates and median salaries anchored to the teacher's enrollment CSV.
"""

import random
import csv
from pathlib import Path
from faker import Faker

random.seed(42)
fake = Faker()
Faker.seed(42)

# ── Output paths ────────────────────────────────────────────────────────────
OUT_DIR = Path(__file__).parent / "mock"
OUT_DIR.mkdir(parents=True, exist_ok=True)

STUDENTS_CSV   = OUT_DIR / "students.csv"
PLACEMENTS_CSV = OUT_DIR / "placements.csv"

# ── Programs (exact names from teacher's enrollment CSV) ─────────────────────
PROGRAMS = [
    "BS Computer Science",
    "BS Data Science",
    "Certificate Data Analytics",
    "MBA Product Management",
    "MS Artificial Intelligence",
    "MS Business Analytics",
    "MS Cloud Computing",
    "MS Computer Science",
    "MS Cybersecurity",
    "MS Data Science",
    "MS Human-Computer Interaction",
    "MS Information Technology",
]

# Per-program lookup: employment_rate (0–1) and median_salary_usd
# Values derived from teacher's enrollment CSV aggregates
PROGRAM_STATS = {
    "BS Computer Science":           {"emp_rate": 0.88, "median_salary": 115_000},
    "BS Data Science":               {"emp_rate": 0.88, "median_salary": 115_000},
    "Certificate Data Analytics":    {"emp_rate": 0.83, "median_salary":  95_000},
    "MBA Product Management":        {"emp_rate": 0.84, "median_salary": 135_000},
    "MS Artificial Intelligence":    {"emp_rate": 0.90, "median_salary": 135_000},
    "MS Business Analytics":         {"emp_rate": 0.87, "median_salary": 110_000},
    "MS Cloud Computing":            {"emp_rate": 0.93, "median_salary": 130_000},
    "MS Computer Science":           {"emp_rate": 0.88, "median_salary": 120_000},
    "MS Cybersecurity":              {"emp_rate": 0.91, "median_salary": 125_000},
    "MS Data Science":               {"emp_rate": 0.89, "median_salary": 125_000},
    "MS Human-Computer Interaction": {"emp_rate": 0.85, "median_salary": 105_000},
    "MS Information Technology":     {"emp_rate": 0.88, "median_salary": 120_000},
}

# Job titles from teacher's job market CSV (33 titles)
JOB_TITLES = [
    "AI Researcher", "Analytics Manager", "Applied Scientist", "BI Analyst",
    "BI Developer", "Backend Developer", "Build Engineer", "CISO",
    "Cloud Architect", "Cloud Consultant", "Data Analyst", "Data Engineer",
    "Data Scientist", "Data Warehouse Architect", "Design Researcher",
    "DevOps Engineer", "Frontend Developer", "Full Stack Developer",
    "Growth PM", "ML Engineer", "MLOps Engineer", "Mobile Developer",
    "Penetration Tester", "Platform Engineer", "Product Designer",
    "Product Manager", "QA Engineer", "Release Manager", "Scrum Master",
    "Security Analyst", "Site Reliability Engineer", "Solutions Architect",
    "UX Researcher",
]

# 30 realistic company names across tech / finance / healthcare / consulting
COMPANIES = [
    "Accenture", "Amazon Web Services", "Bloomberg", "Booz Allen Hamilton",
    "Capital One", "Cisco Systems", "Cognizant", "Deloitte",
    "Epic Systems", "Goldman Sachs", "Google", "IBM",
    "Infosys", "Intel", "JPMorgan Chase", "Johnson & Johnson",
    "KPMG", "Lockheed Martin", "McKinsey & Company", "Microsoft",
    "Morgan Stanley", "Oracle", "Palantir Technologies", "PwC",
    "Raytheon Technologies", "Salesforce", "SAP", "Stripe",
    "UnitedHealth Group", "Visa",
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def placement_status(gpa: float, internships: int, comm_score: int) -> str:
    """Return placement_status label for a placed student."""
    if gpa >= 3.2 and internships >= 1 and comm_score >= 7:
        return "Matched"
    if gpa >= 3.5 and internships == 0:
        return "Overeducated"
    return "Undereducated"


def noisy_salary(median: int) -> float:
    """Return median ± up to 20 % noise, rounded to 2 dp."""
    factor = random.uniform(0.80, 1.20)
    return round(median * factor, 2)


# ── Generate students ─────────────────────────────────────────────────────────

def generate_students(n: int = 3_000) -> list[dict]:
    students = []
    for _ in range(n):
        gpa  = round(random.uniform(2.0, 4.0), 2)
        # Clamp to schema NUMERIC(3,2) max
        gpa  = min(gpa, 4.00)
        comm = random.randint(1, 10)
        prog = random.choice(PROGRAMS)
        students.append({
            "name":               fake.name(),
            "gpa":                gpa,
            "internships":        random.randint(0, 4),
            "projects":           random.randint(0, 10),
            "communication_score": comm,
            "program":            prog,
            "enrollment_year":    random.randint(2019, 2024),
        })
    return students


# ── Generate placements ───────────────────────────────────────────────────────

def placement_probability(s: dict, base_rate: float) -> float:
    """
    Blend programme base rate (60%) with individual feature score (40%).
    Each feature is centred so the overall placement rate stays near base_rate.
    """
    gpa_score    = (s["gpa"] - 2.0) / 2.0 - 0.5                       # range -0.5 to +0.5
    intern_score = min(s["internships"], 4) / 4.0 - 0.5                 # range -0.5 to +0.5
    comm_score   = (s["communication_score"] - 1) / 9.0 - 0.5          # range -0.5 to +0.5
    proj_score   = min(s["projects"], 5) / 5.0 - 0.5                   # range -0.5 to +0.5

    # Weighted individual adjustment (-0.25 to +0.25)
    adj = (0.40 * gpa_score + 0.30 * intern_score +
           0.20 * comm_score + 0.10 * proj_score)

    prob = base_rate + 0.6 * adj
    return min(0.97, max(0.10, prob))


def generate_placements(students: list[dict]) -> list[dict]:
    placements = []
    for idx, s in enumerate(students):
        student_id = idx + 1          # matches DB serial insert order
        stats      = PROGRAM_STATS[s["program"]]
        placed     = random.random() < placement_probability(s, stats["emp_rate"])

        if placed:
            status  = placement_status(s["gpa"], s["internships"], s["communication_score"])
            salary  = noisy_salary(stats["median_salary"])
            company = random.choice(COMPANIES)
            role    = random.choice(JOB_TITLES)
            tth     = random.randint(15, 94)
        else:
            status  = ""              # NULL in CSV → NULL in DB
            salary  = ""
            company = ""
            role    = ""
            tth     = ""

        placements.append({
            "student_id":        student_id,
            "placed":            "true" if placed else "false",
            "placement_status":  status,
            "company":           company,
            "role":              role,
            "salary":            salary,
            "time_to_hire":      tth,
        })
    return placements


# ── Write CSVs ────────────────────────────────────────────────────────────────

def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Generating students …")
    students = generate_students(3_000)
    write_csv(
        STUDENTS_CSV,
        students,
        ["name", "gpa", "internships", "projects", "communication_score", "program", "enrollment_year"],
    )
    print(f"  OK {len(students)} rows -> {STUDENTS_CSV}")

    print("Generating placements ...")
    placements = generate_placements(students)
    placed_count = sum(1 for p in placements if p["placed"] == "true")
    write_csv(
        PLACEMENTS_CSV,
        placements,
        ["student_id", "placed", "placement_status", "company", "role", "salary", "time_to_hire"],
    )
    print(f"  OK {len(placements)} rows ({placed_count} placed, {len(placements)-placed_count} not placed) -> {PLACEMENTS_CSV}")


if __name__ == "__main__":
    main()
