
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

PROCESSED.mkdir(parents=True, exist_ok=True)

files = [
    "patients.csv",
    "encounters.csv",
    "conditions.csv",
    "observations.csv"
]

report = []

for filename in files:
    path = RAW / filename

    report.append("\n" + "=" * 60)
    report.append(f"FILE: {filename}")

    if not path.exists():
        report.append(f"FILE NOT FOUND: {path}")
        continue

    df = pd.read_csv(path, low_memory=False)

    report.append(f"Rows: {len(df)}")
    report.append(f"Columns: {len(df.columns)}")
    report.append(f"Column names: {df.columns.tolist()}")

    report.append("\nData types:")
    report.append(df.dtypes.to_string())

    report.append("\nMissing values:")
    report.append(
        df.isnull().sum()
        .sort_values(ascending=False)
        .to_string()
    )

    report.append("\nFirst 3 records:")
    report.append(df.head(3).to_string(index=False))

    print(f"Inspected {filename}: {len(df)} rows")

output_file = PROCESSED / "schema_report.txt"
output_file.write_text("\n".join(report), encoding="utf-8")

print("\nInspection completed!")
print("Report saved to:", output_file)
