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
import sqlite3, re, argparse, os
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
    # ────────────────────────────────────────────────────────────────────────────────
# Generic dynamic SELECT (joins, expressions, group/order/limit)
# ────────────────────────────────────────────────────────────────────────────────
    def select_dyn(
        self,
        from_table: str,
        columns,
        *,
        joins=None,
        where: str | None = None,
        params: list | tuple | None = None,
        group_by=None,
        order_by: str | None = None,
        limit: int | None = None,
    ):
        """
        Build a SELECT dynamically without hardcoding full SQL.
        - from_table: e.g. "bookings b"
        - columns: list of strings OR (expr, alias) tuples, e.g. ("COUNT(b.booking_id)", "rentals")
        - joins: list[str] like ["JOIN users u ON u.user_id=b.user_id"]
        - where: a single WHERE expression string (use ? placeholders)
        - params: list/tuple of values for placeholders (year, etc.)
        - group_by: list[str] of columns/aliases
        - order_by: string, can reference aliases defined in `columns`
        - limit: optional integer (appended as a bound parameter)
        Returns: list[dict]
        """
        # columns
        col_sql = []
        for col in columns:
            if isinstance(col, (tuple, list)) and len(col) >= 2:
                expr, alias = str(col[0]), str(col[1])
                col_sql.append(f"{expr} AS {alias}")
            else:
                col_sql.append(str(col))

        sql = f"SELECT {', '.join(col_sql)} FROM {from_table}"
        if joins:
            sql += " " + " ".join(joins)
        if where:
            sql += " WHERE " + where
        if group_by:
            if isinstance(group_by, (list, tuple)):
                sql += " GROUP BY " + ", ".join(group_by)
            else:
                sql += " GROUP BY " + str(group_by)
        if order_by:
            sql += " ORDER BY " + order_by
        bind = list(params or [])
        if limit is not None:
            sql += " LIMIT ?"
            bind.append(int(limit))

        cur = self.conn.execute(sql, bind)
        return [dict(r) for r in cur.fetchall()]
    
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

def select_sql(sql: str, params: tuple | list | dict | None = None) -> list[dict]:
    """
    Safe, read-only SELECT runner (single statement). Returns list of dict rows.
    """
    q = (sql or "").strip()
    if not q.lower().startswith("select"):
        raise SqlError("select_sql only allows SELECT statements.")
    if q.count(";") > 0 and not q.endswith(";"):
        raise SqlError("Multiple statements not allowed.")
    cur = repo().conn.execute(q, params or [])
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

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
    seed_admin: bool = True,
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

    if seed_admin:
        maybe_pw = _ensure_admin_superuser(
            r.conn, email=admin_email, name=admin_name, password=admin_pass
        )
        result = {"admin_password": maybe_pw}  # None if not generated
        if maybe_pw:
            print("\n*** Admin password (generated) ***\n" + str(maybe_pw) + "\n")
    return result

def _ensure_admin_superuser(conn, *, email: str, name: str, password: str | None):
    """
    Idempotent: if admin with this email exists, do nothing.
    Returns the generated password if one was created (else None).
    """
    import secrets, hashlib, binascii

    row = conn.execute("SELECT user_id FROM users WHERE email = ?", (email,)).fetchone()
    if row:
        return None  # already present

    if not password:
        password = secrets.token_urlsafe(16)
        generated = password
    else:
        generated = None

    # Hash password compatible with user_repo (PBKDF2-HMAC-SHA256, 200k rounds)
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    pass_hash_hex = binascii.hexlify(dk).decode("ascii")
    salt_hex = binascii.hexlify(salt).decode("ascii")

    conn.execute(
        """INSERT INTO users(email, pass_hash, salt, full_name, role, created_at)
           VALUES (?, ?, ?, ?, 'admin', datetime('now'))""",
        (email, pass_hash_hex, salt_hex, name),
    )
    return generated

def get_args(description: str = "Dod's Cars"):
    default_db = os.environ.get("DODS_CARS_DB", str(Path.cwd() / "dods_cars.sqlite3"))
    default_schema = os.environ.get("DODS_CARS_SCHEMA", "schema.sql")
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--db", default=default_db, help="Path to SQLite DB file")
    ap.add_argument("--schema", default=default_schema, help="Path to schema.sql (if autoinit is used)")
    return ap.parse_args()

# ────────────────────────────────────────────────────────────────────────────────
# Admin Listings (DB layer via dynamic SELECT)
# ────────────────────────────────────────────────────────────────────────────────
def list_all_bookings(status: str | None = None):
    """
    Full booking list (optionally filter by status: pending/approved/rejected).
    Returns rows with joined user & car details.
    """
    where = None
    params = []
    if status:
        where = "b.status = ?"
        params = [status.lower()]
    return repo().select_dyn(
        from_table="bookings b",
        columns=[
            "b.booking_id",
            "b.start_date", "b.end_date", "b.rental_days",
            "b.total_fee", "b.status", "b.created_at",
            "u.user_id", ("u.full_name", "customer_name"), ("u.email", "customer_email"),
            "c.car_id", ("c.year", "car_year"), ("c.make", "car_make"), ("c.model", "car_model"),
        ],
        joins=[
            "JOIN users u ON u.user_id = b.user_id",
            "JOIN cars  c ON c.car_id  = b.car_id",
        ],
        where=where,
        params=params,
        order_by="b.created_at DESC, b.start_date DESC, b.booking_id DESC",
    )

def list_all_maintenance(status: str | None = None):
    """
    Full maintenance list (optionally filter by status: open/closed).
    We treat 'open' as end_date IS NULL; 'closed' as end_date NOT NULL.
    """
    where = None
    params = []
    if status:
        s = status.lower()
        if s == "open":
            where = "m.end_date IS NULL"
        elif s == "closed":
            where = "m.end_date IS NOT NULL"

    return repo().select_dyn(
        from_table="maintenance m",
        columns=[
            "m.maint_id", "m.type", "m.cost", "m.start_date", "m.end_date", "m.notes",
            "c.car_id", ("c.year", "car_year"), ("c.make", "car_make"), ("c.model", "car_model"),
        ],
        joins=["JOIN cars c ON c.car_id = m.car_id"],
        where=where,
        params=params,
        order_by="m.start_date DESC, m.maint_id DESC",
    )


# ────────────────────────────────────────────────────────────────────────────────
# Analytics (DB layer) using dynamic SELECT
# ────────────────────────────────────────────────────────────────────────────────
def _year_bounds(year: int):
    start = f"{year:04d}-01-01"
    end   = f"{year+1:04d}-01-01"  # exclusive upper bound
    return start, end

def _year_bounds(year: int):
    return f"{year:04d}-01-01", f"{year+1:04d}-01-01"  # [start, exclusive_end)

def analytics_top_users(year: int, limit: int = 5):
    y0, y1 = _year_bounds(year)
    rows = repo().select_dyn(
        from_table="bookings b",
        columns=[
            "u.user_id", "u.full_name", "u.email",
            ("COUNT(b.booking_id)", "rentals"),
            ("COALESCE(SUM(b.total_fee),0.0)", "revenue"),
        ],
        joins=["JOIN users u ON u.user_id = b.user_id"],
        where="LOWER(b.status)='approved' AND b.start_date >= ? AND b.start_date < ?",
        params=[y0, y1],
        group_by=["u.user_id"],
        order_by="revenue DESC, rentals DESC, u.full_name",
        limit=limit,
    )
    return rows

def analytics_top_car_revenue(year: int, limit: int = 5):
    y0, y1 = _year_bounds(year)
    return repo().select_dyn(
        from_table="bookings b",
        columns=[
            "c.car_id", "c.year", "c.make", "c.model",
            ("COUNT(b.booking_id)", "rentals"),
            ("COALESCE(SUM(b.total_fee),0.0)", "revenue"),
        ],
        joins=["JOIN cars c ON c.car_id = b.car_id"],
        where="LOWER(b.status)='approved' AND b.start_date >= ? AND b.start_date < ?",
        params=[y0, y1],
        group_by=["c.car_id"],
        order_by="revenue DESC, rentals DESC, c.make, c.model",
        limit=limit,
    )

def analytics_highest_maint_cost(year: int, limit: int = 5):
    y0, y1 = _year_bounds(year)
    return repo().select_dyn(
        from_table="maintenance m",
        columns=[
            "c.car_id", "c.year", "c.make", "c.model",
            ("COUNT(m.maint_id)", "jobs"),
            ("COALESCE(SUM(m.cost),0.0)", "total_cost"),
            ("COALESCE(AVG(m.cost),0.0)", "avg_cost"),
        ],
        joins=["JOIN cars c ON c.car_id = m.car_id"],
        where="m.start_date >= ? AND m.start_date < ?",
        params=[y0, y1],
        group_by=["c.car_id"],
        order_by="total_cost DESC, jobs DESC, c.make, c.model",
        limit=limit,
    )

def analytics_most_rented_cars(*, start: str|None, end: str|None, limit: int):
    where = ["LOWER(b.status)='approved'"]
    params = []
    if start:
        where.append("b.end_date >= ?"); params.append(start)
    if end:
        where.append("b.start_date <= ?"); params.append(end)
    rows = repo().select_dyn(
        from_table="bookings b",
        columns=[
            "c.car_id", "c.year", "c.make", "c.model",
            ("COUNT(1)", "rentals"),
            ("COALESCE(SUM(b.rental_days),0)", "days"),
        ],
        joins=["JOIN cars c ON c.car_id = b.car_id"],
        where=" AND ".join(where),
        params=params,
        group_by=["c.car_id"],
        order_by="rentals DESC, days DESC, c.year DESC, c.make ASC, c.model ASC",
        limit=limit,
    )
    return rows

def analytics_monthly_revenue(*, year: int|None, start: str|None, end: str|None):
    where = ["LOWER(b.status)='approved'"]
    params = []
    if year is not None:
        y0, y1 = _year_bounds(year)
        where.append("b.start_date >= ? AND b.start_date < ?")
        params += [y0, y1]
    if start:
        where.append("b.end_date >= ?"); params.append(start)
    if end:
        where.append("b.start_date <= ?"); params.append(end)
    return repo().select_dyn(
        from_table="bookings b",
        columns=[
            ("strftime('%Y-%m', b.start_date)", "ym"),
            ("COALESCE(SUM(b.total_fee),0)", "revenue"),
            ("COUNT(1)", "bookings"),
        ],
        where=" AND ".join(where),
        params=params,
        group_by=["strftime('%Y-%m', b.start_date)"],  # avoid alias in GROUP BY
        order_by="ym ASC",
    )

def analytics_avg_rental_duration(*, start: str|None, end: str|None):
    where = ["LOWER(b.status)='approved'"]
    params = []
    if start:
        where.append("b.end_date >= ?"); params.append(start)
    if end:
        where.append("b.start_date <= ?"); params.append(end)
    rows = repo().select_dyn(
        from_table="bookings b",
        columns=[("AVG(b.rental_days)", "avg_days")],
        where=" AND ".join(where),
        params=params,
    )
    v = rows[0].get("avg_days") if rows else None
    return round(v, 2) if v is not None else None

def analytics_maintenance_summary(*, start: str|None, end: str|None):
    where = ["1=1"]
    params = []
    if start:
        where.append("m.start_date >= ?"); params.append(start)
    if end:
        where.append("(m.end_date IS NULL OR m.end_date <= ?)"); params.append(end)
    return repo().select_dyn(
        from_table="maintenance m",
        columns=[
            "c.car_id", "c.year", "c.make", "c.model",
            ("COALESCE(SUM(m.cost),0)", "maint_cost"),
            ("SUM(CAST((julianday(COALESCE(m.end_date, date('now'))) - julianday(m.start_date)) AS INTEGER))", "downtime_days"),
        ],
        joins=["JOIN cars c ON c.car_id = m.car_id"],
        where=" AND ".join(where),
        params=params,
        group_by=["c.car_id"],
        order_by="maint_cost DESC, downtime_days DESC, c.year DESC",
    )

def analytics_latest_year_with_data():
    row = repo().conn.execute(
        "SELECT MAX(strftime('%Y', start_date)) FROM bookings WHERE status='approved'"
    ).fetchone()
    return int(row[0]) if row and row[0] else None

# ────────────────────────────────────────────────────────────────────────────────
# Diagnostics & robust helpers for analytics
# ────────────────────────────────────────────────────────────────────────────────

_SQL_DEBUG = False
def set_sql_debug(flag: bool = True):
    """Enable/disable SQL debug printing for select_dyn."""
    global _SQL_DEBUG
    _SQL_DEBUG = bool(flag)

# Patch select_dyn to print SQL (only if you control it here).
# If select_dyn already exists, add the two lines guarded by _SQL_DEBUG.
def select_dyn(self_or_repo, from_table, columns, *, joins=None, where=None,
               params=None, group_by=None, order_by=None, limit=None):
    # If you already have a select_dyn method on SqlRepo, IGNORE this wrapper
    # and instead add the _SQL_DEBUG print where you build 'sql' and 'bind'.
    raise NotImplementedError("Hook _SQL_DEBUG prints into your existing select_dyn")

def _print_sql_debug(sql: str, bind: list | tuple):
    if _SQL_DEBUG:
        print("\n[sql_repo] SQL:\n" + sql.strip())
        print("[sql_repo] params:", list(bind))

def analytics_debug_counts():
    """Quick visibility: DB path, counts, min/max dates."""
    r = repo()
    print(f"[sql_repo] DB file: {getattr(r, 'db_path', '(unknown)')}")
    c = r.conn
    try:
        total_b = c.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
        appr_b  = c.execute("SELECT COUNT(*) FROM bookings WHERE LOWER(status)='approved'").fetchone()[0]
        rng_b   = c.execute("SELECT MIN(start_date), MAX(start_date) FROM bookings").fetchone()
        total_m = c.execute("SELECT COUNT(*) FROM maintenance").fetchone()[0]
        rng_m   = c.execute("SELECT MIN(start_date), MAX(start_date) FROM maintenance").fetchone()
        print(f"[sql_repo] bookings: total={total_b}, approved={appr_b}, range={rng_b[0]}..{rng_b[1]}")
        print(f"[sql_repo] maint:    total={total_m}, range={rng_m[0]}..{rng_m[1]}")
    except Exception as e:
        print(f"[sql_repo] debug error: {e}")

def analytics_years_with_data():
    """Years that have APPROVED bookings (strings like '2022', '2023', ...)."""
    q = "SELECT DISTINCT substr(start_date,1,4) AS y FROM bookings WHERE LOWER(status)='approved' ORDER BY y"
    cur = repo().conn.execute(q)
    return [int(r["y"]) for r in cur.fetchall() if r["y"] and r["y"].isdigit()]

def analytics_latest_year_with_data():
    ys = analytics_years_with_data()
    return ys[-1] if ys else None