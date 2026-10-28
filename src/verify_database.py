
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "healthinsight.db"

expected = {
    "patients": 1163,
    "encounters": 61459,
    "conditions": 38094,
    "observations": 5311144,
}

with sqlite3.connect(DB) as conn:
    for table, expected_count in expected.items():
        actual = conn.execute(
            f'SELECT COUNT(*) FROM "{table}"'
        ).fetchone()[0]

        status = "OK" if actual == expected_count else "CHECK"

        print(
            f"{table}: {actual:,} rows "
            f"(expected {expected_count:,}) - {status}"
        )

print("\nVerification finished.")
