"""
Builds data/processed/features.parquet directly from data/mock/students.csv
and data/mock/placements.csv — no database connection required.

Replicates the same transforms as ml/feature_engineering.py:
  - MinMaxScaler on gpa and communication_score
  - One-hot encode program (prefix prog_)
  - Encode placement_status to int
  - Merge students + placements
"""
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler
import joblib

ROOT      = Path(__file__).parent.parent
MOCK_DIR  = ROOT / "data" / "mock"
OUT_DIR   = ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

STATUS_ENCODE = {"Matched": 2, "Overeducated": 1, "Undereducated": 0}

def main():
    print("Building features.parquet from mock CSVs ...")

    students   = pd.read_csv(MOCK_DIR / "students.csv")
    placements = pd.read_csv(MOCK_DIR / "placements.csv")

    students["student_id"] = range(1, len(students) + 1)

    df = students.merge(placements, on="student_id", how="left")

    df["placed"] = df["placed"].astype(bool).astype(int)

    df["placement_status_encoded"] = (
        df["placement_status"].map(STATUS_ENCODE).fillna(-1).astype(int)
    )

    scaler = MinMaxScaler()
    df[["gpa_scaled", "communication_score_scaled"]] = scaler.fit_transform(
        df[["gpa", "communication_score"]]
    )
    joblib.dump(scaler, OUT_DIR / "scaler.pkl")

    dummies = pd.get_dummies(df["program"], prefix="prog").astype(int)
    df = pd.concat([df, dummies], axis=1)

    prog_cols = sorted([c for c in df.columns if c.startswith("prog_")])
    feature_cols = (
        ["student_id", "enrollment_year",
         "gpa", "gpa_scaled",
         "internships", "projects",
         "communication_score", "communication_score_scaled",
         "placed", "placement_status_encoded",
         "salary", "time_to_hire"]
        + prog_cols
    )
    df = df[feature_cols]

    out_path = OUT_DIR / "features.parquet"
    df.to_parquet(out_path, index=False)

    placed = df["placed"].sum()
    print(f"  Rows    : {len(df)}")
    print(f"  Columns : {df.shape[1]}")
    print(f"  Placed  : {placed} ({placed/len(df)*100:.1f}%)")
    print(f"  Saved   -> {out_path}")

    print("\nFeature correlation with placement (sanity check):")
    for col in ["gpa_scaled", "internships", "projects", "communication_score_scaled"]:
        r = df[col].corr(df["placed"])
        print(f"  {col:<36}  r = {r:+.4f}")

if __name__ == "__main__":
    main()
