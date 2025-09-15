#!/usr/bin/env python3
"""
Bootstrap SQLite database (schema only, no data).

Usage:
  python create_db.py --db dods_cars.sqlite3
"""
import argparse, sqlite3, sys, pathlib

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="dods_cars.sqlite3", help="SQLite file path")
    ap.add_argument("--schema", default="schema.sql", help="Schema SQL file")
    args = ap.parse_args()

    db_path = pathlib.Path(args.db)
    schema_path = pathlib.Path(args.schema)

    sql = schema_path.read_text(encoding="utf-8")

    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(sql)
        conn.commit()
        print(f"Created/updated schema in {db_path}")
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())
