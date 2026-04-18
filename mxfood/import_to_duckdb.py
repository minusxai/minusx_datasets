#!/usr/bin/env python3
"""Import all generated CSVs into a DuckDB database file."""

import os
import argparse
import duckdb

# Columns that should be treated as timestamps
TIMESTAMP_COLUMNS = {
    "created_at",
    "updated_at",
    "order_time",
    "event_timestamp",
    "started_at",
    "ended_at",
    "valid_from",
    "valid_until",
    "used_at",
    "attributed_at",
    "assigned_at",
    "picked_up_at",
    "delivered_at",
    "resolved_at",
    "sent_at",
    "opened_at",
    "converted_at",
    "closed_at",
}

# Columns that should be treated as dates (not timestamps)
DATE_COLUMNS = {
    "start_date",
    "end_date",
    "date",
    "hire_date",
    "termination_date",
    "shift_date",
    "order_date",
    "issued_date",
    "due_date",
    "paid_date",
    "month",
}


def get_csv_files(output_dir: str) -> list[str]:
    """Get all CSV files in the output directory."""
    csv_files = []
    for f in os.listdir(output_dir):
        if f.endswith(".csv") and f != "summary.csv":
            csv_files.append(f)
    return sorted(csv_files)


def import_csv_to_duckdb(con: duckdb.DuckDBPyConnection, csv_path: str, table_name: str):
    """Import a CSV file into DuckDB with proper type handling."""

    # First, let DuckDB auto-detect and create the table
    con.execute(f"""
        CREATE OR REPLACE TABLE {table_name} AS
        SELECT * FROM read_csv_auto('{csv_path}', header=true, ignore_errors=true)
    """)

    # Get column info
    columns = con.execute(f"DESCRIBE {table_name}").fetchall()

    # Build list of columns that need timestamp conversion
    conversions = []
    for col_name, col_type, *_ in columns:
        if col_name in TIMESTAMP_COLUMNS and "VARCHAR" in col_type.upper():
            conversions.append((col_name, "TIMESTAMP"))
        elif col_name in DATE_COLUMNS and "VARCHAR" in col_type.upper():
            conversions.append((col_name, "DATE"))

    # Apply conversions if needed
    if conversions:
        for col_name, target_type in conversions:
            try:
                con.execute(f"""
                    ALTER TABLE {table_name}
                    ALTER COLUMN {col_name}
                    SET DATA TYPE {target_type}
                    USING TRY_CAST({col_name} AS {target_type})
                """)
            except Exception as e:
                print(f"    Warning: Could not convert {col_name} to {target_type}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Import generated CSVs into a DuckDB database"
    )
    parser.add_argument(
        "-i", "--input",
        default="output",
        help="Input directory containing CSV files (default: output)"
    )
    parser.add_argument(
        "-o", "--output",
        default="mxfood.duckdb",
        help="Output DuckDB file (default: mxfood.duckdb)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing database file"
    )

    args = parser.parse_args()

    # Check input directory
    if not os.path.exists(args.input):
        print(f"Error: Input directory '{args.input}' does not exist")
        return 1

    # Check if output exists
    if os.path.exists(args.output) and not args.overwrite:
        print(f"Error: Output file '{args.output}' already exists. Use --overwrite to replace.")
        return 1

    # Remove existing file if overwriting
    if os.path.exists(args.output) and args.overwrite:
        os.remove(args.output)

    # Get CSV files
    csv_files = get_csv_files(args.input)
    if not csv_files:
        print(f"No CSV files found in '{args.input}'")
        return 1

    print(f"Importing {len(csv_files)} tables into {args.output}")
    print("-" * 50)

    # Connect to DuckDB
    con = duckdb.connect(args.output)

    # Import each CSV
    for csv_file in csv_files:
        table_name = csv_file.replace(".csv", "")
        csv_path = os.path.join(args.input, csv_file)

        try:
            import_csv_to_duckdb(con, csv_path, table_name)
            row_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"  ✓ {table_name:<30} {row_count:>10,} rows")
        except Exception as e:
            print(f"  ✗ {table_name:<30} Error: {e}")

    # Print summary
    print("-" * 50)

    # Show table info
    tables = con.execute("SHOW TABLES").fetchall()
    total_rows = 0
    for (table_name,) in tables:
        count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        total_rows += count

    print(f"Total: {len(tables)} tables, {total_rows:,} rows")
    print(f"Database saved to: {os.path.abspath(args.output)}")

    con.close()
    return 0


if __name__ == "__main__":
    exit(main())
