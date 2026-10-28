
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DB_PATH = ROOT / "healthinsight.db"

CHUNK_SIZE = 50_000

# Keep only the patient fields needed for analytics.
# Direct identifiers and street addresses are excluded.
TABLES = {
    "patients": {
        "file": "patients.csv",
        "columns": [
            "Id", "BIRTHDATE", "DEATHDATE",
            "MARITAL", "RACE", "ETHNICITY", "GENDER",
            "CITY", "STATE", "COUNTY",
            "HEALTHCARE_EXPENSES", "HEALTHCARE_COVERAGE"
        ],
        "chunksize": None,
    },
    "encounters": {
        "file": "encounters.csv",
        "columns": None,
        "chunksize": None,
    },
    "conditions": {
        "file": "conditions.csv",
        "columns": None,
        "chunksize": None,
    },
    "observations": {
        "file": "observations.csv",
        "columns": None,
        "chunksize": CHUNK_SIZE,
    },
}

def clean_column_names(df):
    df.columns = [
        col.strip().lower() for col in df.columns
    ]
    return df

def load_table(conn, table, config):
    path = RAW / config["file"]

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}"
        )

    print(f"\nLoading {table}...")

    # Drop an existing table so reruns don't duplicate data.
    conn.execute(f'DROP TABLE IF EXISTS "{table}"')

    total_rows = 0
    chunksize = config["chunksize"]

    if chunksize is None:
        df = pd.read_csv(
            path,
            usecols=config["columns"],
            dtype=str,
            low_memory=False
        )
        df = clean_column_names(df)

        df.to_sql(
            table,
            conn,
            if_exists="replace",
            index=False
        )

        total_rows = len(df)

    else:
        first_chunk = True

        for chunk in pd.read_csv(
            path,
            chunksize=chunksize,
            dtype=str,
            low_memory=False
        ):
            chunk = clean_column_names(chunk)

            chunk.to_sql(
                table,
                conn,
                if_exists=(
                    "replace" if first_chunk else "append"
                ),
                index=False,
                chunksize=5000
            )

            first_chunk = False
            total_rows += len(chunk)

            print(
                f"  Loaded {total_rows:,} rows...",
                flush=True
            )

    print(f"Completed {table}: {total_rows:,} rows")
    return total_rows

def main():
    counts = {}

    # Use a transaction so a failed load can be rolled back.
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")

        try:
            for table, config in TABLES.items():
                counts[table] = load_table(
                    conn, table, config
                )

            print("\nCreating indexes...")

            indexes = [
                """
                CREATE INDEX IF NOT EXISTS
                idx_encounters_patient
                ON encounters(patient)
                """,
                """
                CREATE INDEX IF NOT EXISTS
                idx_conditions_patient
                ON conditions(patient)
                """,
                """
                CREATE INDEX IF NOT EXISTS
                idx_conditions_encounter
                ON conditions(encounter)
                """,
                """
                CREATE INDEX IF NOT EXISTS
                idx_observations_patient
                ON observations(patient)
                """,
                """
                CREATE INDEX IF NOT EXISTS
                idx_observations_encounter
                ON observations(encounter)
                """,
            ]

            for sql in indexes:
                conn.execute(sql)

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        print("\nDATABASE VERIFICATION")
        print("=" * 45)

        for table in TABLES:
            count = conn.execute(
                f'SELECT COUNT(*) FROM "{table}"'
            ).fetchone()[0]

            print(f"{table}: {count:,} rows")

    print(f"\nDatabase created at:\n{DB_PATH}")

if __name__ == "__main__":
    main()
