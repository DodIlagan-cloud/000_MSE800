#!/usr/bin/env python3

"""
Assessment 1 - Car System - Dod's Cars
PSEASS - EJI
Eduardo JR Ilagan

sql_repo.py — Generic dynamic SQL repository for SQLite.
- Centralizes SELECT/INSERT/UPDATE/DELETE and view queries
- Parameterizes values and **whitelists identifiers** (tables/columns) by introspecting schema
- Safe dynamic WHERE builder supporting operators: eq, ne, lt, lte, gt, gte, like, in, isnull, notnull
"""
from __future__ import annotations
import sqlite3, re, argparse
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from pathlib import Path
from datetime import datetime

# --- Require non-empty values for INSERTs ---
_REQUIRE_NONEMPTY_ON_INSERT = True  # default on; toggle with set_insert_require_nonempty()

def set_insert_require_nonempty(enabled: bool = True):
    """Globally require that every column you pass in an INSERT has a non-empty value."""
    global _REQUIRE_NONEMPTY_ON_INSERT
    _REQUIRE_NONEMPTY_ON_INSERT = bool(enabled)

def _is_blank(v) -> bool:
    return v is None or (isinstance(v, str) and v.strip() == "")

def _enforce_nonempty_on_insert(table: str, values: dict) -> dict:
    """
    Raise SqlError if any provided INSERT value is None/blank string.
    Returns a cleaned dict (stripped strings).
    """
    if not _REQUIRE_NONEMPTY_ON_INSERT:
        return values
    cleaned = {}
    for col, val in values.items():
        if _is_blank(val):
            raise SqlError(f"{table}.{col} is required and cannot be empty.")
        cleaned[col] = val.strip() if isinstance(val, str) else val
    return cleaned

OP_MAP = {
    "eq": "=",
    "ne": "!=",
    "lt": "<",
    "lte": "<=",
    "gt": ">",
    "gte": ">=",
    "like": "LIKE",
}

class SqlError(Exception):
    pass

class SqlRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        try:
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON")
        except sqlite3.DatabaseError as e:
            raise SqlError(str(e))
        self._schema = self._introspect_schema()

    # for test data setup 
    def insert(self, table: str, values: dict) -> int:
        try:
            values = _enforce_nonempty_on_insert(table, values)  # <-- add this line
            sql, params = self._build_insert_sql(table, values)
            cur = self.conn.execute(sql, params)
            return cur.lastrowid
        except sqlite3.IntegrityError as e:
            raise SqlError(f"Integrity error on {table}: {e}")
        except sqlite3.DatabaseError as e:
            raise SqlError(f"DB error on {table}: {e}")
    # ---------- Connection helpers ----------
    @staticmethod
    def open_db(db_path: str) -> sqlite3.Connection:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def require_tables(conn: sqlite3.Connection, names: Sequence[str]):
        missing = []
        for n in names:
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE (type='table' OR type='view') AND name=?",
                (n,),
            )
            if cur.fetchone() is None:
                missing.append(n)
        if missing:
            raise SqlError(f"Missing tables/views: {', '.join(missing)}")

    # ---------- Schema cache & whitelisting ----------
    def _introspect_schema(self) -> Dict[str, set]:
        schema: Dict[str, set] = {}
        cur = self.conn.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','view')")
        for row in cur.fetchall():
            name = row["name"]
            try:
                cols = self.conn.execute(f"PRAGMA table_info({name})").fetchall()
                schema[name] = {c["name"] for c in cols}
            except sqlite3.DatabaseError:
                # Fallback: allow no columns if PRAGMA fails
                schema[name] = set()
        return schema

    def _assert_table(self, table: str):
        if table not in self._schema:
            # lazy refresh in case schema changed
            self._schema = self._introspect_schema()
            if table not in self._schema:
                raise SqlError(f"Unknown table/view: {table}")

    def _assert_columns(self, table: str, cols: Iterable[str]):
        allowed = self._schema.get(table, set())
        for c in cols:
            if c not in allowed and c != "*":
                raise SqlError(f"Unknown column for {table}: {c}")

    # ---------- WHERE builder ----------
    def _build_where(self, table: str, where: Optional[Dict[str, Any]]):
        if not where:
            return "", {}
        clauses = []
        params: Dict[str, Any] = {}
        idx = 0
        for key, val in where.items():
            idx += 1
            if "__" in key:
                col, op = key.split("__", 1)
            else:
                col, op = key, "eq"
            self._assert_columns(table, [col])
            tag = f"p{idx}"
            if op == "in":
                if not isinstance(val, (list, tuple, set)) or len(val) == 0:
                    clauses.append("1=0")
                    continue
                ph = ",".join([f":{tag}_{i}" for i, _ in enumerate(val)])
                for i, v in enumerate(val):
                    params[f"{tag}_{i}"] = v
                clauses.append(f"{col} IN ({ph})")
            elif op == "isnull":
                clauses.append(f"{col} IS NULL")
            elif op == "notnull":
                clauses.append(f"{col} IS NOT NULL")
            else:
                sql_op = OP_MAP.get(op.lower())
                if not sql_op:
                    raise SqlError(f"Unsupported operator: {op}")
                clauses.append(f"{col} {sql_op} :{tag}")
                params[tag] = val
        return " WHERE " + " AND ".join(clauses), params

    # ---------- SELECT ----------
    def select(
        self,
        table: str,
        where: Optional[Dict[str, Any]] = None,
        columns: Optional[Sequence[str]] = None,
        order: Optional[Sequence[Tuple[str, str]]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[dict]:
        self._assert_table(table)
        cols = ["*"] if not columns else list(columns)
        self._assert_columns(table, [c for c in cols if c != "*"])
        sql = [f"SELECT {', '.join(cols)} FROM {table}"]
        where_sql, params = self._build_where(table, where)
        sql.append(where_sql)
        if order:
            order_parts = []
            for col, direction in order:
                d = direction.upper()
                if d not in ("ASC", "DESC"):
                    raise SqlError("Order direction must be ASC or DESC")
                self._assert_columns(table, [col])
                order_parts.append(f"{col} {d}")
            sql.append(" ORDER BY " + ", ".join(order_parts))
        if limit is not None:
            if not isinstance(limit, int) or limit < 0:
                raise SqlError("limit must be a non-negative integer")
            sql.append(" LIMIT :_limit")
            params["_limit"] = limit
        if offset is not None:
            if not isinstance(offset, int) or offset < 0:
                raise SqlError("offset must be a non-negative integer")
            sql.append(" OFFSET :_offset")
            params["_offset"] = offset
        cur = self.conn.execute("".join(sql), params)
        return [dict(r) for r in cur.fetchall()]

    def select_one(
        self,
        table: str,
        where: Optional[Dict[str, Any]] = None,
        columns: Optional[Sequence[str]] = None,
        order: Optional[Sequence[Tuple[str, str]]] = None,
    ) -> Optional[dict]:
        rows = self.select(table, where=where, columns=columns, order=order, limit=1)
        return rows[0] if rows else None

    def exists(self, table: str, where: Dict[str, Any]) -> bool:
        row = self.select_one(table, where=where, columns=["1 as x"])
        return row is not None

    # ---------- INSERT ----------
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        self._assert_table(table)
        cols = list(data.keys())
        self._assert_columns(table, cols)
        placeholders = [f":{c}" for c in cols]
        sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(placeholders)})"
        cur = self.conn.execute(sql, data)
        return cur.lastrowid

    # ---------- UPDATE ----------
    def update(self, table: str, where: Dict[str, Any], changes: Dict[str, Any]) -> int:
        self._assert_table(table)
        if not changes:
            return 0
        sets = []
        params = {}
        for i, (col, val) in enumerate(changes.items(), start=1):
            self._assert_columns(table, [col])
            tag = f"s{i}"
            sets.append(f"{col} = :{tag}")
            params[tag] = val
        where_sql, wparams = self._build_where(table, where)
        params.update(wparams)
        sql = f"UPDATE {table} SET {', '.join(sets)}{where_sql}"
        cur = self.conn.execute(sql, params)
        return cur.rowcount

    # ---------- DELETE ----------
    def delete(self, table: str, where: Dict[str, Any]) -> int:
        self._assert_table(table)
        where_sql, params = self._build_where(table, where)
        if not where_sql.strip():
            raise SqlError("Refusing to delete without WHERE clause")
        sql = f"DELETE FROM {table}{where_sql}"
        cur = self.conn.execute(sql, params)
        return cur.rowcount

    # ---------- VIEW (alias for select) ----------
    def view(
        self,
        view_name: str,
        where: Optional[Dict[str, Any]] = None,
        columns: Optional[Sequence[str]] = None,
        order: Optional[Sequence[Tuple[str, str]]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[dict]:
        return self.select(view_name, where=where, columns=columns, order=order, limit=limit, offset=offset)
    

# ---------- Global repository management (singleton) ----------
_DB_PATH = None
_CONN = None
_REPO = None

def configure(db_path: str) -> "SqlRepo":
    """Configure global DB path and open a shared connection/repo."""
    global _DB_PATH, _CONN, _REPO
    if not db_path:
        raise SqlError("db_path is required")

    p = Path(db_path)

    # If they passed a directory, drop the file inside it
    if p.exists() and p.is_dir():
        p = p / "dods_cars.sqlite3"

    # Make sure the parent folder exists
    p.parent.mkdir(parents=True, exist_ok=True)

    # Reuse if already configured to the same file
    if _REPO is not None and _DB_PATH == str(p):
        return _REPO

    # Close any existing connection
    if _CONN:
        try:
            _CONN.close()
        except Exception:
            pass

    # Open connection (wrap in helpful error)
    try:
        conn = sqlite3.connect(str(p))  # convert Path -> str for Windows
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
    except sqlite3.OperationalError as e:
        raise SqlError(
            f"Unable to open database file at '{p}'. "
            f"Check that the folder exists and you have write permission. Original: {e}"
        )

    _DB_PATH = str(p)
    _CONN = conn
    _REPO = SqlRepo(_CONN)
    return _REPO

def repo() -> "SqlRepo":
    """Return the configured global SqlRepo."""
    if _REPO is None:
        raise SqlError("SqlRepo not configured. Call configure(db_path) first.")
    return _REPO

def close():
    """Close the global connection (optional)."""
    global _CONN, _REPO, _DB_PATH
    if _CONN:
        try:
            _CONN.close()
        except Exception:
            pass
    _CONN = None
    _REPO = None
    _DB_PATH = None

def require_tables_configured(names):
    r = repo()
    SqlRepo.require_tables(r.conn, names)

# ---------- CLI helpers (optional) ----------
def cli_argparser(description: str | None = None):
    """Return an argparse.ArgumentParser with a standard --db option."""
    default_db = str(Path(__file__).resolve().parent / "data" / "dods_cars.sqlite3")
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--db", default=default_db, help="Path to SQLite DB file")
    return p

def cli_configure(argv=None, description: str | None = None):
    """Parse --db and call configure(); returns argparse.Namespace."""
    p = cli_argparser(description)
    args = p.parse_args(argv)
    configure(args.db)
    return args

def get_args(argv=None, description: str | None = None):
    """Parse CLI args (standard --db) and return argparse.Namespace."""
    p = cli_argparser(description)
    return p.parse_args(argv)

# ---------- Validation Checks for Inputs ----------

def prompt_required_text(label: str) -> str:
    while True:
        s = input(f"{label}: ").strip()
        if s:
            return s
        print(f"{label} is required.")

def prompt_required_int(label: str) -> int:
    while True:
        s = input(f"{label}: ").strip()
        if not s:
            print(f"{label} is required.")
            continue
        try:
            return int(s)
        except ValueError:
            print(f"{label} must be an integer.")

def prompt_required_float(label: str) -> float:
    while True:
        s = input(f"{label}: ").strip()
        if not s:
            print(f"{label} is required.")
            continue
        try:
            return float(s)
        except ValueError:
            print(f"{label} must be a number.")

def prompt_required_date(label: str, fmt: str = "YYYY-MM-DD") -> str:
    """Returns the original string in YYYY-MM-DD after validation."""
    while True:
        s = input(f"{label} ({fmt}): ").strip()
        if not s:
            print(f"{label} is required.")
            continue
        try:
            datetime.strptime(s, fmt)
            return s
        except ValueError:
            print(f"{label} must match {fmt}.")

"""Bootstrap -     
    Portable first-run init using schema.sql + seed_db.py.
    - configure(db_path) if provided (else assume already configured)
    - if 'users'/'cars' missing, exec schema.sql (same effect as create_db.py)
    - if seed=True, call seed_db.ensure_admin(...) and seed_db.seed_cars(...)
      (idempotent for admin; cars are seeded only if table is empty)
    Safe to call every start.
    """
def _read_schema(schema_path: str | None) -> str:
    # Use provided path first; fall back to schema.sql next to this file
    if schema_path:
        p = Path(schema_path)
        if p.exists():
            return p.read_text(encoding="utf-8")
    fallback = Path(__file__).with_name("schema.sql")
    if fallback.exists():
        return fallback.read_text(encoding="utf-8")
    raise SqlError("schema.sql not found. Provide a valid schema_path.")

def autoinit(
    db_path: str | None = None,
    *,
    schema_path: str | None = "schema.sql",
    seed: bool = False,
    admin_email: str = "admin@rental.local",
    admin_name: str = "Admin Superuser",
    admin_pass: str | None = None,
):

    if db_path is not None:
        configure(db_path)

    r = repo()  # raises if not configured

    # Create schema only if tables are missing
    try:
        SqlRepo.require_tables(r.conn, ["users", "cars"])
    except SqlError:
        sql = _read_schema(schema_path)
        with r.conn:
            r.conn.executescript(sql)

    # Assert again (fail fast if schema.sql was wrong or not found)
    SqlRepo.require_tables(r.conn, ["users", "cars"])

    if seed:
        try:
            # Reuse your seed functions
            from seed_db import ensure_admin, seed_cars  # your existing script
            with r.conn:
                uid, maybe_pw = ensure_admin(r.conn, admin_email, admin_name, admin_pass)
                # Seed cars only if empty to avoid duplicates
                if r.conn.execute("SELECT COUNT(1) FROM cars").fetchone()[0] == 0:
                    seed_cars(r.conn)
            if maybe_pw:
                print("\n*** Admin password (generated) ***\n" + str(maybe_pw) + "\n")
            return {"admin_user_id": uid, "admin_password": maybe_pw}
        except Exception as e:
            # Don't break app start if seed script isn't available
            print(f"[autoinit] Seeding skipped or failed: {e}")
    return None