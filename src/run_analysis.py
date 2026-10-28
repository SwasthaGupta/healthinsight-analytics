
from pathlib import Path
import sqlite3
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

DB_PATH = ROOT / "healthinsight.db"
SQL_PATH = ROOT / "sql" / "analysis.sql"
OUTPUT_DIR = ROOT / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if not DB_PATH.exists():
    raise FileNotFoundError(
        f"Database not found: {DB_PATH}"
    )

if not SQL_PATH.exists():
    raise FileNotFoundError(
        f"SQL file not found: {SQL_PATH}"
    )

# Read the SQL file
sql_text = SQL_PATH.read_text(encoding="utf-8")

# Separate queries using semicolons
statements = [
    statement.strip()
    for statement in sql_text.split(";")
    if statement.strip()
]

with sqlite3.connect(DB_PATH) as conn:
    for index, statement in enumerate(statements, start=1):

        # Extract the query name from its first comment
        match = re.search(
            r"^\s*--\s*(.+)",
            statement
        )

        query_name = (
            match.group(1).strip()
            if match
            else f"query_{index}"
        )

        # Remove SQL comments before execution
        clean_sql = re.sub(
            r"(?m)^\s*--.*$",
            "",
            statement
        ).strip()

        if not clean_sql:
            continue

        print("\n" + "=" * 55)
        print(query_name)

        # Execute the query and collect its results
        result = pd.read_sql_query(clean_sql, conn)

        print(result.to_string(index=False))

        # Create a safe filename
        safe_name = re.sub(
            r"[^a-zA-Z0-9_-]+",
            "_",
            query_name
        ).strip("_").lower()

        output_file = (
            OUTPUT_DIR / f"{index:02d}_{safe_name}.csv"
        )

        result.to_csv(output_file, index=False)

        print(f"\nSaved results: {output_file.name}")

print("\nAll SQL queries executed successfully!")
