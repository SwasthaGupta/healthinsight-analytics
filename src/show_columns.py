
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

for filename in [
    "patients.csv",
    "encounters.csv",
    "conditions.csv",
    "observations.csv"
]:
    path = RAW / filename

    # Read only the header, not the complete dataset
    df = pd.read_csv(path, nrows=0)

    print(f"\n{filename}")
    print("-" * 50)

    for column in df.columns:
        print(column)
