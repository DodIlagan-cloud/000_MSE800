#!/usr/bin/env python3
"""
sql_repo.py — Generic dynamic SQL repository for SQLite (Dod’s Cars)

What this module provides
- Single place for all DB access (Singleton connection + SqlRepo)
- Dynamic, parameterised SELECT/INSERT/UPDATE/DELETE with identifier whitelisting
- Safe WHERE builder (eq, ne, lt, lte, gt, gte, like, in, isnull, notnull)
- First-run bootstrap (schema.sql) + admin-only seeding
- Admin listings (bookings, maintenance)
- Analytics helpers (top users, top car revenue, maintenance cost, etc.)

This file is intentionally framework-free and CLI-safe.
"""

from __future__ import annotations
import argparse
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from datetime import datetime, date
from contextlib import contextmanager
from dataclasses import dataclass

# ────────────────────────────────────────────────────────────────────────────────
# Configuration & Globals
# ────────────────────────────────────────────────────────────────────────────────

APP_DIR_NAME = "DodCars"
DB_FILE_NAME = "dods_cars.sqlite3"

# Toggle: require non-empty values for INSERTs (prevents accidental NULLs/blanks)
_REQUIRE_NONEMPTY_ON_INSERT = True

# Toggle: print SQL statements (for local debugging only)
_SQL_DEBUG = False


def set_insert_require_nonempty(enabled: bool = True) -> None:
    """Globally require every INSERT value to be non-empty (None/'' rejected)."""
    global _REQUIRE_NONEMPTY_ON_INSERT
    _REQUIRE_NONEMPTY_ON_INSERT = bool(enabled)


def set_sql_debug(flag: bool = True) -> None:
    """Enable/disable SQL debug printing for dynamic selects."""
    global _SQL_DEBUG
    _SQL_DEBUG = bool(flag)


def _print_sql_debug(sql: str, bind: Sequence[Any]) -> None:
    if _SQL_DEBUG:
        print("\n[sql_repo] SQL:\n" + sql.strip())
        print("[sql_repo] params:", list(bind))


def appdata_dir() -> Path:
    """Per-user application-data directory."""
    if os.name == "nt":  # Windows
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home() / "AppData/Local")
        return Path(base) / APP_DIR_NAME
    else:  # macOS/Linux
        base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local/share")
        return Path(base) / APP_DIR_NAME


def default_db_path() -> str:
    p = appdata_dir()
    p.mkdir(parents=True, exist_ok=True)
    return str(p / DB_FILE_NAME)

def ranges_overlap(a1: date, a2: date, b1: date, b2: date) -> bool:
    """
    Return True if two [start, end) date ranges overlap.
    Logic: overlap exists if a1 < b2 and a2 > b1.
    """
    return a1 < b2 and a2 > b1

class SqlError(Exception):
    pass


def _is_blank(v: Any) -> bool:
    return v is None or (isinstance(v, str) and v.strip() == "")


def _enforce_nonempty_on_insert(table: str, values: Dict[str, Any]) -> Dict[str, Any]:
    """Raise SqlError if any provided INSERT value is None/blank; strip strings."""
    if not _REQUIRE_NONEMPTY_ON_INSERT:
        return values
    cleaned: Dict[str, Any] = {}
    for col, val in values.items():
        if _is_blank(val):
            raise SqlError(f"{table}.{col} is required and cannot be empty.")
        cleaned[col] = val.strip() if isinstance(val, str) else val
    return cleaned


# ────────────────────────────────────────────────────────────────────────────────
# Core repository (dynamic SQL with identifier whitelisting)
# ────────────────────────────────────────────────────────────────────────────────

OP_MAP = {
    "eq": "=",
    "ne": "!=",
    "lt": "<",
    "lte": "<=",
    "gt": ">",
    "gte": ">=",
    "like": "LIKE",
}


class SqlRepo:

    # ---- Singleton instance + accessor (explicit, at module top) ----
    _sql_repo_singleton: SqlRepo | None = None
    
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        try:
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON;")
            self.conn.execute("PRAGMA journal_mode = WAL;")
            self.conn.execute("PRAGMA synchronous = NORMAL;")
        except sqlite3.DatabaseError as e:
            raise SqlError(str(e))
        self._schema = self._introspect_schema()

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
                schema[name] = set()
        return schema
    
    @staticmethod
    def require_tables(conn: sqlite3.Connection, names: Sequence[str]) -> None:
        """
        Verify that the given tables/views exist. Raises SqlError if any are missing.
        """
        missing: list[str] = []
        for n in names:
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name=?",
                (n,),
            )
            if cur.fetchone() is None:
                missing.append(n)
        if missing:
            raise SqlError(f"Missing tables/views: {', '.join(missing)}")

    def _assert_table(self, table: str) -> None:
        if table not in self._schema:
            self._schema = self._introspect_schema()  # lazy refresh
            if table not in self._schema:
                raise SqlError(f"Unknown table/view: {table}")

    def _assert_columns(self, table: str, cols: Iterable[str]) -> None:
        allowed = self._schema.get(table, set())
        for c in cols:
            if c not in allowed and c != "*":
                raise SqlError(f"Unknown column for {table}: {c}")

    # ---------- WHERE builder ----------
    def _build_where(self, table: str, where: Optional[Dict[str, Any]]):
        if not where:
            return "", {}
        clauses: List[str] = []
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
                placeholders = ",".join([f":{tag}_{i}" for i, _ in enumerate(val)])
                for i, v in enumerate(val):
                    params[f"{tag}_{i}"] = v
                clauses.append(f"{col} IN ({placeholders})")
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

    # ---------- Dynamic SELECT (joins/expr/group/order/limit) ----------
    def select_dyn(
        self,
        from_table: str,
        columns: Sequence[str | Tuple[str, str]],
        *,
        joins: Optional[Sequence[str]] = None,
        where: Optional[str] = None,
        params: Optional[Sequence[Any]] = None,
        group_by: Optional[Sequence[str] | str] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[dict]:
        col_sql: List[str] = []
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
        _print_sql_debug(sql, bind)
        cur = self.conn.execute(sql, bind)
        return [dict(r) for r in cur.fetchall()]

    # ---------- CRUD ----------
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
            parts = []
            for col, direction in order:
                d = direction.upper()
                if d not in ("ASC", "DESC"):
                    raise SqlError("Order direction must be ASC or DESC")
                self._assert_columns(table, [col])
                parts.append(f"{col} {d}")
            sql.append(" ORDER BY " + ", ".join(parts))
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
        q = "".join(sql)
        _print_sql_debug(q, list(params.values()) if isinstance(params, dict) else [])
        cur = self.conn.execute(q, params)
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

    def insert(self, table: str, values: Dict[str, Any]) -> int:
        self._assert_table(table)
        values = _enforce_nonempty_on_insert(table, values)
        cols = list(values.keys())
        self._assert_columns(table, cols)
        placeholders = [f":{c}" for c in cols]
        sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(placeholders)})"
        _print_sql_debug(sql, [values[c] for c in cols])
        cur = self.conn.execute(sql, values)
        return cur.lastrowid

    def update(self, table: str, where: Dict[str, Any], changes: Dict[str, Any]) -> int:
        self._assert_table(table)
        if not changes:
            return 0
        sets = []
        params: Dict[str, Any] = {}
        for i, (col, val) in enumerate(changes.items(), start=1):
            self._assert_columns(table, [col])
            tag = f"s{i}"
            sets.append(f"{col} = :{tag}")
            params[tag] = val
        where_sql, wparams = self._build_where(table, where)
        params.update(wparams)
        sql = f"UPDATE {table} SET {', '.join(sets)}{where_sql}"
        _print_sql_debug(sql, list(params.values()))
        cur = self.conn.execute(sql, params)
        return cur.rowcount

    def delete(self, table: str, where: Dict[str, Any]) -> int:
        self._assert_table(table)
        where_sql, params = self._build_where(table, where)
        if not where_sql.strip():
            raise SqlError("Refusing to delete without WHERE clause")
        sql = f"DELETE FROM {table}{where_sql}"
        _print_sql_debug(sql, list(params.values()))
        cur = self.conn.execute(sql, params)
        return cur.rowcount

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


# ────────────────────────────────────────────────────────────────────────────────
# Singleton connection management
# ────────────────────────────────────────────────────────────────────────────────

_DB_PATH: Optional[str] = None
_CONN: Optional[sqlite3.Connection] = None
_REPO: Optional[SqlRepo] = None

@dataclass
class _Session:
    user: Optional[Any] = None  # holds the signed-in user object

# Single, process-wide session instance
session = _Session()

# Convenience helpers (optional)
def login_user(u: Any) -> None:
    session.user = u

def logout_user() -> None:
    session.user = None

def current_user() -> Optional[Any]:
    return session.user

def configure(db_path: str) -> SqlRepo:
    """Configure global DB path and open a shared connection/repo."""
    global _DB_PATH, _CONN, _REPO
    if not db_path:
        raise SqlError("db_path is required")
    p = Path(db_path)
    if p.exists() and p.is_dir():
        p = p / DB_FILE_NAME
    p.parent.mkdir(parents=True, exist_ok=True)
    if _REPO is not None and _DB_PATH == str(p):
        return _REPO
    if _CONN:
        try:
            _CONN.close()
        except Exception:
            pass
    try:
        conn = sqlite3.connect(str(p))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
    except sqlite3.OperationalError as e:
        raise SqlError(f"Unable to open database file at '{p}'. {e}")
    _DB_PATH = str(p)
    _CONN = conn
    _REPO = SqlRepo(_CONN)
    return _REPO


def repo() -> SqlRepo:
    if _REPO is None:
        raise SqlError("SqlRepo not configured. Call configure(db_path) first.")
    return _REPO


def close() -> None:
    global _CONN, _REPO, _DB_PATH
    if _CONN:
        try:
            _CONN.close()
        except Exception:
            pass
    _CONN = None
    _REPO = None
    _DB_PATH = None

@contextmanager
def transaction():
    """
    Atomic transaction on the shared connection (repo().conn).
    Group multiple repo updates; commit on success, roll back on error.
    """
    conn = repo().conn
    try:
        conn.execute("BEGIN")
        yield
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise

def require_tables_configured(names: Sequence[str]) -> None:
    r = repo()
    SqlRepo.require_tables(r.conn, names)  # type: ignore[attr-defined]


def select_sql(sql: str, params: Sequence[Any] | Dict[str, Any] | None = None) -> List[dict]:
    """Safe, read-only SELECT runner (single statement)."""
    q = (sql or "").strip()
    if not q.lower().startswith("select"):
        raise SqlError("select_sql only allows SELECT statements.")
    if ";" in q and not q.endswith(";"):
        raise SqlError("Multiple statements not allowed.")
    cur = repo().conn.execute(q, params or [])
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


# ────────────────────────────────────────────────────────────────────────────────
# CLI helpers
# ────────────────────────────────────────────────────────────────────────────────

def get_args(description: str = "Dod's Cars"):
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--db", default=default_db_path(), help="Path to SQLite DB file")
    return ap.parse_args()


# ────────────────────────────────────────────────────────────────────────────────
# Input validators (used by menus)
# ────────────────────────────────────────────────────────────────────────────────

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
            print(f"{label} is required."); continue
        try:
            return int(s)
        except ValueError:
            print(f"{label} must be an integer.")


def prompt_required_float(label: str) -> float:
    while True:
        s = input(f"{label}: ").strip()
        if not s:
            print(f"{label} is required."); continue
        try:
            return float(s)
        except ValueError:
            print(f"{label} must be a number.")


def prompt_required_date(label: str, fmt: str = "%Y-%m-%d") -> str:
    """Validate ISO date; returns the original string."""
    while True:
        s = input(f"{label} (YYYY-MM-DD): ").strip()
        if not s:
            print(f"{label} is required."); continue
        try:
            datetime.strptime(s, fmt)
            return s
        except ValueError:
            print(f"{label} must match YYYY-MM-DD.")


# ────────────────────────────────────────────────────────────────────────────────
# Bootstrap (schema + admin-only seed)
# ────────────────────────────────────────────────────────────────────────────────

def _read_schema(schema_path: Optional[str]) -> str:
    if schema_path:
        p = Path(schema_path)
        if p.exists():
            return p.read_text(encoding="utf-8")
    fallback = Path(__file__).with_name("schema.sql")
    if fallback.exists():
        return fallback.read_text(encoding="utf-8")
    raise SqlError("schema.sql not found. Provide a valid schema_path.")


def autoinit(
    db_path: Optional[str] = None,
    *,
    schema_path: Optional[str] = "schema.sql",
    seed_admin: bool = True,
    admin_pass: Optional[str] = None,
) -> None:
    """
    Ensure DB is present, schema applied, and (optionally) an admin superuser exists.
    - If db_path provided, calls configure(db_path). Else assumes already configured.
    - Applies schema.sql only when core tables are missing.
    - Seeds ONLY the Admin Superuser if no admin exists.
    """
    if db_path is not None:
        configure(db_path)
    r = repo()
    first_run = False
    try:
        SqlRepo.require_tables(r.conn, ["users", "cars"])  # type: ignore[attr-defined]
    except Exception:
        sql = _read_schema(schema_path)
        with r.conn:
            r.conn.executescript(sql)
        first_run = True
    # Validate schema now exists
    SqlRepo.require_tables(r.conn, ["users", "cars"])  # type: ignore[attr-defined]
    if seed_admin:
        _seed_admin_superuser_if_missing(r.conn, password=admin_pass, echo=first_run)


def _seed_admin_superuser_if_missing(conn: sqlite3.Connection, *, password: Optional[str], echo: bool = False) -> None:
    """
    Create a single Admin Superuser if none exists.
    Prefers user_repo.UserRepo().auth_signup for consistency; falls back to PBKDF2.
    """
    have_admin = conn.execute("SELECT 1 FROM users WHERE role='admin' LIMIT 1").fetchone()
    if have_admin:
        return
    email = "admin@dods.local"
    name = "Admin Superuser"
    try:
        import user_repo  # local import to avoid cycles at module load
        ur = user_repo.UserRepo()
        existing = ur.get_by_email(email)
        if existing is None:
            ur.auth_signup(email=email, full_name=name, password=password or "Admin#123", role="admin")
        else:
            if getattr(existing, "role", "customer") != "admin":
                conn.execute("UPDATE users SET role='admin' WHERE user_id=?", (existing.id,))
                conn.commit()
        if echo:
            print("Seeded Admin Superuser via user_repo: admin@dods.local / Admin#123 (change on first login)")
    except Exception:
        # Fallback PBKDF2 impl
        import hashlib, secrets, binascii
        pw = password or "Admin#123"
        salt = secrets.token_bytes(16)
        dk = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt, 200_000)
        pass_hash = binascii.hexlify(dk).decode("ascii")
        salt_hex = binascii.hexlify(salt).decode("ascii")
        conn.execute(
            "INSERT INTO users (email, pass_hash, salt, full_name, role, created_at) "
            "VALUES (?, ?, ?, ?, 'admin', datetime('now'))",
            (email, pass_hash, salt_hex, name),
        )
        conn.commit()
        if echo:
            print("Seeded Admin Superuser (fallback): admin@dods.local / Admin#123 (change on first login)")


# ────────────────────────────────────────────────────────────────────────────────
# Admin listings (read-only joins)
# ────────────────────────────────────────────────────────────────────────────────

def list_all_bookings(status: Optional[str] = None) -> List[dict]:
    where = None
    params: List[Any] = []
    if status:
        where = "LOWER(b.status) = ?"
        params = [status.lower()]
    return repo().select_dyn(
        from_table="bookings b",
        columns=[
            "b.booking_id", "b.start_date", "b.end_date", "b.rental_days",
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


def list_all_maintenance(status: Optional[str] = None) -> List[dict]:
    where = None
    params: List[Any] = []
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
# Analytics (read-only)
# ────────────────────────────────────────────────────────────────────────────────

def _year_bounds(year: int) -> Tuple[str, str]:
    return f"{year:04d}-01-01", f"{year+1:04d}-01-01"  # [start, exclusive_end)


def analytics_top_users(year: int, limit: int = 5) -> List[dict]:
    y0, y1 = _year_bounds(year)
    return repo().select_dyn(
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


def analytics_top_car_revenue(year: int, limit: int = 5) -> List[dict]:
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


def analytics_highest_maint_cost(year: int, limit: int = 5) -> List[dict]:
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


def analytics_most_rented_cars(*, start: Optional[str], end: Optional[str], limit: int) -> List[dict]:
    where = ["LOWER(b.status)='approved'"]
    params: List[Any] = []
    if start:
        where.append("b.end_date >= ?"); params.append(start)
    if end:
        where.append("b.start_date <= ?"); params.append(end)
    return repo().select_dyn(
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


def analytics_monthly_revenue(*, year: Optional[int], start: Optional[str], end: Optional[str]) -> List[dict]:
    where = ["LOWER(b.status)='approved'"]
    params: List[Any] = []
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
        group_by=["strftime('%Y-%m', b.start_date)"],
        order_by="ym ASC",
    )


def analytics_avg_rental_duration(*, start: Optional[str], end: Optional[str]) -> Optional[float]:
    where = ["LOWER(b.status)='approved'"]
    params: List[Any] = []
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


def analytics_maintenance_summary(*, start: Optional[str], end: Optional[str]) -> List[dict]:
    where = ["1=1"]
    params: List[Any] = []
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


def analytics_years_with_data() -> List[int]:
    q = "SELECT DISTINCT substr(start_date,1,4) AS y FROM bookings WHERE LOWER(status)='approved' ORDER BY y"
    cur = repo().conn.execute(q)
    return [int(r["y"]) for r in cur.fetchall() if r["y"] and str(r["y"]).isdigit()]


def analytics_latest_year_with_data() -> Optional[int]:
    ys = analytics_years_with_data()
    return ys[-1] if ys else None


def analytics_debug_counts() -> None:
    """Quick visibility: row counts and date ranges."""
    c = repo().conn
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
