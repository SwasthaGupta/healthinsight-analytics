
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "healthinsight.db"

with sqlite3.connect(DB_PATH) as conn:
    # List all database tables
    tables = conn.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
    """).fetchall()

    print("Database tables:")
    for table in tables:
        print("-", table[0])

    # Check patient and encounter counts
    for table in ["patients", "encounters", "conditions"]:
        count = conn.execute(
            f'SELECT COUNT(*) FROM "{table}"'
        ).fetchone()[0]

        print(f"{table}: {count:,}")

    # Test a simple analytical query
    result = conn.execute("""
        SELECT
            ENCOUNTERCLASS,
            COUNT(*) AS encounter_count
        FROM encounters
        GROUP BY ENCOUNTERCLASS
        ORDER BY encounter_count DESC
    """)

    print("\nEncounter types:")
    for row in result:
        print(row)

print("\nDatabase test completed.")
