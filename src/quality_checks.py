
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 100_000

# Store only the identifiers needed for relationship checks.
patients = pd.read_csv(
    RAW / "patients.csv",
    usecols=["Id"],
    dtype=str
)
encounters = pd.read_csv(
    RAW / "encounters.csv",
    usecols=["Id", "PATIENT", "START", "STOP"],
    dtype=str
)

patient_ids = set(patients["Id"].dropna())
encounter_ids = set(encounters["Id"].dropna())

issues = []
missing_rows = []
summary = []

def add_issue(table, check, count, details=""):
    issues.append({
        "table": table,
        "check": check,
        "issue_count": int(count),
        "details": details
    })

def record_missing(table, filename, columns):
    """Count missing values without loading huge tables at once."""
    totals = {}
    rows = 0

    for chunk in pd.read_csv(
        RAW / filename,
        chunksize=CHUNK_SIZE,
        low_memory=False
    ):
        rows += len(chunk)
        for col in columns:
            if col in chunk.columns:
                totals[col] = (
                    totals.get(col, 0)
                    + int(chunk[col].isna().sum())
                )

    for col, count in totals.items():
        missing_rows.append({
            "table": table,
            "column": col,
            "row_count": rows,
            "missing_count": count,
            "missing_pct": round(
                100 * count / rows, 2
            ) if rows else 0
        })

    return rows, totals

# --------------------------------------------------
# 1. PATIENTS
# --------------------------------------------------
df = pd.read_csv(RAW / "patients.csv", dtype=str)

add_issue(
    "patients",
    "Duplicate patient IDs",
    df["Id"].duplicated().sum()
)

add_issue(
    "patients",
    "Missing patient IDs",
    df["Id"].isna().sum()
)

record_missing(
    "patients",
    "patients.csv",
    ["BIRTHDATE", "GENDER", "RACE", "ETHNICITY",
     "CITY", "STATE", "ZIP", "DEATHDATE"]
)

summary.append({
    "table": "patients",
    "row_count": len(df),
    "column_count": len(df.columns)
})

# --------------------------------------------------
# 2. ENCOUNTERS
# --------------------------------------------------
df = pd.read_csv(RAW / "encounters.csv", dtype=str)

add_issue(
    "encounters",
    "Duplicate encounter IDs",
    df["Id"].duplicated().sum()
)

add_issue(
    "encounters",
    "Missing encounter IDs",
    df["Id"].isna().sum()
)

add_issue(
    "encounters",
    "Unknown patient references",
    (~df["PATIENT"].isin(patient_ids)).sum()
)

start = pd.to_datetime(df["START"], errors="coerce")
stop = pd.to_datetime(df["STOP"], errors="coerce")

add_issue(
    "encounters",
    "Invalid or missing start dates",
    start.isna().sum()
)

add_issue(
    "encounters",
    "Invalid or missing stop dates",
    stop.isna().sum()
)

add_issue(
    "encounters",
    "Stop date before start date",
    (stop.notna() & start.notna() & (stop < start)).sum()
)

record_missing(
    "encounters",
    "encounters.csv",
    ["PATIENT", "START", "STOP", "ORGANIZATION",
     "PROVIDER", "TOTAL_CLAIM_COST"]
)

summary.append({
    "table": "encounters",
    "row_count": len(df),
    "column_count": len(df.columns)
})

# --------------------------------------------------
# 3. CONDITIONS — process in chunks
# --------------------------------------------------
condition_rows = 0
condition_unknown_patients = 0
condition_unknown_encounters = 0
condition_missing = {}

for chunk in pd.read_csv(
    RAW / "conditions.csv",
    chunksize=CHUNK_SIZE,
    dtype=str
):
    condition_rows += len(chunk)

    condition_unknown_patients += int(
        (~chunk["PATIENT"].isin(patient_ids)).sum()
    )

    condition_unknown_encounters += int(
        (
            chunk["ENCOUNTER"].notna()
            & ~chunk["ENCOUNTER"].isin(encounter_ids)
        ).sum()
    )

    for col in ["START", "PATIENT", "ENCOUNTER", "CODE"]:
        if col in chunk.columns:
            condition_missing[col] = (
                condition_missing.get(col, 0)
                + int(chunk[col].isna().sum())
            )

add_issue(
    "conditions",
    "Unknown patient references",
    condition_unknown_patients
)

add_issue(
    "conditions",
    "Unknown non-null encounter references",
    condition_unknown_encounters
)

for col, count in condition_missing.items():
    missing_rows.append({
        "table": "conditions",
        "column": col,
        "row_count": condition_rows,
        "missing_count": count,
        "missing_pct": round(
            100 * count / condition_rows, 2
        ) if condition_rows else 0
    })

summary.append({
    "table": "conditions",
    "row_count": condition_rows,
    "column_count": 6
})

# --------------------------------------------------
# 4. OBSERVATIONS — 5.3M rows, chunked processing
# --------------------------------------------------
observation_rows = 0
observation_unknown_patients = 0
observation_unknown_encounters = 0
observation_missing = {}
invalid_observation_dates = 0

for chunk in pd.read_csv(
    RAW / "observations.csv",
    chunksize=CHUNK_SIZE,
    dtype=str,
    low_memory=False
):
    observation_rows += len(chunk)

    observation_unknown_patients += int(
        (~chunk["PATIENT"].isin(patient_ids)).sum()
    )

    observation_unknown_encounters += int(
        (
            chunk["ENCOUNTER"].notna()
            & ~chunk["ENCOUNTER"].isin(encounter_ids)
        ).sum()
    )

    parsed_dates = pd.to_datetime(
        chunk["DATE"], errors="coerce"
    )
    invalid_observation_dates += int(
        parsed_dates.isna().sum()
    )

    for col in ["DATE", "PATIENT", "ENCOUNTER",
                "CATEGORY", "CODE", "DESCRIPTION", "VALUE"]:
        if col in chunk.columns:
            observation_missing[col] = (
                observation_missing.get(col, 0)
                + int(chunk[col].isna().sum())
            )

add_issue(
    "observations",
    "Unknown patient references",
    observation_unknown_patients
)

add_issue(
    "observations",
    "Unknown non-null encounter references",
    observation_unknown_encounters
)

add_issue(
    "observations",
    "Invalid or missing observation dates",
    invalid_observation_dates
)

for col, count in observation_missing.items():
    missing_rows.append({
        "table": "observations",
        "column": col,
        "row_count": observation_rows,
        "missing_count": count,
        "missing_pct": round(
            100 * count / observation_rows, 2
        ) if observation_rows else 0
    })

summary.append({
    "table": "observations",
    "row_count": observation_rows,
    "column_count": 9
})

# --------------------------------------------------
# 5. SAVE REPORTS
# --------------------------------------------------
pd.DataFrame(issues).to_csv(
    OUT / "quality_issues.csv", index=False
)

pd.DataFrame(missing_rows).to_csv(
    OUT / "missing_values_report.csv", index=False
)

pd.DataFrame(summary).to_csv(
    OUT / "dataset_summary.csv", index=False
)

print("\nDATA QUALITY CHECKS COMPLETED")
print("=" * 45)
print(pd.DataFrame(summary).to_string(index=False))
print("\nReports saved in:", OUT)
print("- quality_issues.csv")
print("- missing_values_report.csv")
print("- dataset_summary.csv")
