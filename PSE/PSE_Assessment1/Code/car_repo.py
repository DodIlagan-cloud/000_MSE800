#!/usr/bin/env python3
"""
Assessment 1 - Car System - Dod's Cars
PSEASS - EJI
Eduardo JR Ilagan

booking_repo.py — Booking & Charges Repository (no raw sqlite3)

Purpose
- Encapsulate all Booking/Charge data access and business rules.
- Keep UI/menus DB-free: callers use methods here; SQL lives in sql_repo.

Design
- Pattern: Repository + (injected) Factory (ABC) for row→object mapping
- Transactions: callers may group multi-step ops with sql_repo.transaction()
- Conflict Policy: creation is lenient; approval is strict (see UC-15)

Use-Case Mapping
- UC-04 Create Booking
  • create_pending(user_id, car_id, start_date, end_date, extras=None)
  • calculates base fee (UC-06 include); extras optional
- UC-05 View Booking Status
  • get(booking_id), list_by_user(user_id)
- UC-06 Calculate Fees (include)
  • _calc_fee(...), charges_for(...), add_charge(...), recalc(...)
- UC-08 Approve/Reject Booking
  • approve(booking_id) — only from 'pending' → 'approved'
  • reject(booking_id, reason=None) — only from 'pending' → 'rejected'
- UC-15 Check Maintenance Conflicts (include)
  • approve(...) enforces:
      - no overlap with maintenance windows (CarRepo.maint_overlaps)
      - no overlap with existing APPROVED bookings (car_has_overlap)

Key Rules
- Availability checks for customers (UC-03) exclude maintenance + APPROVED bookings.
  Pending bookings do not block (demand is captured; enforced at approval).
- Fee = daily_rate * days + sum(extras); totals rounded to 2 dp.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, List, Dict, Any, Tuple

from base_repo import CarFactoryABC
from sql_repo import repo as _repo, SqlError, ranges_overlap   # ranges_overlap centralized here

# ────────────────────────────────────────────────────────────────────────────────
# Errors
# ────────────────────────────────────────────────────────────────────────────────
class RepoError(Exception): ...
class DomainError(Exception): ...

# ────────────────────────────────────────────────────────────────────────────────
# Local helpers
# ────────────────────────────────────────────────────────────────────────────────
def _parse_date(d: str | date) -> date:
    if isinstance(d, date):
        return d
    try:
        return datetime.strptime(d, "%Y-%m-%d").date()
    except Exception:
        raise DomainError("Dates must be 'YYYY-MM-DD'.")

def _days(start: date, end: date) -> int:
    n = (end - start).days
    if n <= 0:
        raise DomainError("end_date must be after start_date.")
    return n

# ────────────────────────────────────────────────────────────────────────────────
# Domain classes
# ────────────────────────────────────────────────────────────────────────────────
@dataclass
class Car:
    id: Optional[int]
    make: str
    model: str
    year: int
    color: Optional[str]
    mileage: Optional[int]
    daily_rate: float
    available_now: int
    min_days: int
    max_days: int

    def label(self) -> str:
        return f"{self.year} {self.make} {self.model}"

    def validate_days(self, days: int):
        if days < self.min_days:
            raise DomainError(f"Minimum rental days is {self.min_days}.")
        if days > self.max_days:
            raise DomainError(f"Maximum rental days is {self.max_days}.")

@dataclass
class Maint:
    id: Optional[int]
    car_id: int
    type: str
    cost: Optional[float]
    start_date: date
    end_date: Optional[date]
    notes: Optional[str]

    def active(self) -> bool:
        return self.end_date is None

    def overlaps(self, s: date, e: date) -> bool:
        """
        True if this maintenance window overlaps [s, e).
        Open maint (end_date=None) is treated as ongoing (date.max).
        """
        m_end = self.end_date or date.max
        return ranges_overlap(self.start_date, m_end, s, e)

# ────────────────────────────────────────────────────────────────────────────────
# Default Factory (keeps your original row→object mapping logic)
# ────────────────────────────────────────────────────────────────────────────────
class _DefaultCarFactory(CarFactoryABC):
    def car_from_row(self, r: Dict[str, Any]) -> Car:
        return Car(
            id=r.get("car_id"), make=r["make"], model=r["model"], year=r["year"],
            color=r.get("color"), mileage=r.get("mileage"), daily_rate=r["daily_rate"],
            available_now=r["available_now"], min_days=r["min_rent_days"], max_days=r["max_rent_days"]
        )
    def maintenance_from_row(self, r: Dict[str, Any]) -> Maint:
        sd = _parse_date(r["start_date"])
        ed = _parse_date(r["end_date"]) if r.get("end_date") else None
        return Maint(
            id=r.get("maint_id"), car_id=r["car_id"], type=r["type"], cost=r.get("cost"),
            start_date=sd, end_date=ed, notes=r.get("notes")
        )

# ==============================================================================
# CarRepo — AFTER (uses CarFactoryABC for mapping; business rules unchanged)
# ==============================================================================
class CarRepo:
    """
    Cars & Maintenance repository.
    - UC-03: available_in_range(...)
    - UC-10/11: maint_open(...), maint_close(...)
    - UC-13/14: block/unblock represented by open/close maintenance
    - UC-15: maint_overlaps(...)
    """

    def __init__(self, factory: CarFactoryABC | None = None):
        self.sql = _repo()
        self._f: CarFactoryABC = factory or _DefaultCarFactory()

    # ──────────────────────────────────────────────────────────────────────
    # Cars CRUD
    # ──────────────────────────────────────────────────────────────────────
    def get(self, car_id: int) -> Optional[Car]:
        r = self.sql.select_one("cars", where={"car_id__eq": car_id})
        return self._f.car_from_row(r) if r else None

    def list(self, **filters) -> List[Car]:
        where: Dict[str, Any] = {}
        if "make" in filters:  where["make__like"] = f"%{filters['make']}%"
        if "model" in filters: where["model__like"] = f"%{filters['model']}%"
        if "year_min" in filters: where["year__gte"] = int(filters["year_min"])
        if "year_max" in filters: where["year__lte"] = int(filters["year_max"])
        if "available" in filters: where["available_now__eq"] = 1 if filters["available"] else 0
        rows = self.sql.select("cars", where=where, order=[("year","DESC"), ("make","ASC"), ("model","ASC")])
        return [self._f.car_from_row(r) for r in rows]

    def create(self, car: Car) -> Car:
        data = {
            "make": car.make, "model": car.model, "year": car.year, "color": car.color,
            "mileage": car.mileage, "daily_rate": car.daily_rate, "available_now": car.available_now,
            "min_rent_days": car.min_days, "max_rent_days": car.max_days
        }
        new_id = self.sql.insert("cars", data)
        car.id = new_id
        return car

    def save(self, car: Car) -> int:
        if not car.id:
            raise RepoError("Car id required for update.")
        changes = {
            "make": car.make, "model": car.model, "year": car.year, "color": car.color,
            "mileage": car.mileage, "daily_rate": car.daily_rate, "available_now": car.available_now,
            "min_rent_days": car.min_days, "max_rent_days": car.max_days
        }
        return self.sql.update("cars", where={"car_id__eq": car.id}, changes=changes)

    def delete(self, car_id: int) -> int:
        return self.sql.delete("cars", where={"car_id__eq": car_id})

    # ──────────────────────────────────────────────────────────────────────
    # Maintenance (UC-10 / UC-11)
    # ──────────────────────────────────────────────────────────────────────
    def maint_open(
        self,
        car_id: int, type: str, start_date: str | date,
        *, cost: Optional[float] = None, notes: Optional[str] = None
    ) -> Maint:
        s = _parse_date(start_date)
        mid = self.sql.insert("maintenance", {
            "car_id": car_id, "type": type, "cost": cost, "start_date": s.isoformat(),
            "end_date": None, "notes": notes
        })
        return Maint(mid, car_id, type, cost, s, None, notes)

    def maint_close(self, maint_id: int, end_date: str | date | None = None, notes: Optional[str] = None) -> int:
        e = _parse_date(end_date) if end_date else date.today()
        changes: Dict[str, Any] = {"end_date": e.isoformat()}
        if notes is not None:
            changes["notes"] = notes
        return self.sql.update("maintenance", where={"maint_id__eq": maint_id}, changes=changes)

    def maint_active_for_car(self, car_id: int) -> List[Maint]:
        rows = self.sql.select("maintenance", where={"car_id__eq": car_id, "end_date__isnull": True})
        return [self._f.maintenance_from_row(r) for r in rows]

    def maint_get(self, maint_id: int) -> Optional[Maint]:
        r = self.sql.select_one("maintenance", where={"maint_id__eq": maint_id})
        return self._f.maintenance_from_row(r) if r else None

    def maint_list(
        self,
        *,
        active_only: bool | None = None,    # True=open only, False=closed only, None=all
        car_id: int | None = None,
        sort: str = "start_desc",           # 'start_desc' | 'start_asc'
    ) -> List[Maint]:
        where: dict[str, object] = {}
        if car_id is not None:
            where["car_id__eq"] = car_id
        if active_only is True:
            where["end_date__isnull"] = True
        elif active_only is False:
            where["end_date__isnull"] = False
        order = [("start_date", "DESC" if sort.endswith("desc") else "ASC")]
        rows = self.sql.select("maintenance", where=where, order=order)
        return [self._f.maintenance_from_row(r) for r in rows]

    # ──────────────────────────────────────────────────────────────────────
    # Conflicts & Availability (UC-03, UC-15 include)
    # ──────────────────────────────────────────────────────────────────────
    def maint_overlaps(self, car_id: int, start_date: str | date, end_date: str | date) -> bool:
        """
        True if any maintenance window for the car overlaps [start_date, end_date).
        """
        s, e = _parse_date(start_date), _parse_date(end_date)
        rows = self.sql.select("maintenance", where={
            "car_id__eq": car_id,
            "start_date__lt": e.isoformat(),  # prefilter; exact overlap via entity method
        })
        for r in rows:
            m = self._f.maintenance_from_row(r)
            if m.overlaps(s, e):
                return True
        return False

    def available_in_range(
        self,
        start_date: str | date,
        end_date: str | date,
        *,
        min_days: Optional[int] = None,
        max_days: Optional[int] = None
    ) -> List[Car]:
        """
        UC-03: return cars available in [start, end) that satisfy:
          - per-car rental policy (min/max days), and
          - NO overlap with (a) maintenance windows, (b) APPROVED bookings.
        Note: PENDING bookings do not block; conflicts are enforced at approval.
        """
        s, e = _parse_date(start_date), _parse_date(end_date)
        days = _days(s, e)

        rows = self.sql.select("cars", where={"available_now__eq": 1})
        cars = [self._f.car_from_row(r) for r in rows]

        # Filter by requested vs per-car policy
        out: List[Car] = []
        from booking_repo import BookingRepo   # lazy import to avoid cycles
        bkr = BookingRepo()
        for c in cars:
            # optional explicit filters first
            if min_days is not None and days < min_days: 
                continue
            if max_days is not None and days > max_days:
                continue
            # enforce per-car policy
            try:
                c.validate_days(days)
            except DomainError:
                continue
            # conflicts (UC-15)
            if self.maint_overlaps(c.id, s, e):
                continue
            if bkr.car_has_overlap(c.id, s, e):   # APPROVED bookings only
                continue
            out.append(c)
        return out