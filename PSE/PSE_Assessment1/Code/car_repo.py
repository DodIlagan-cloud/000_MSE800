#!/usr/bin/env python3
"""
Assessment 1 - Car System - Dod's Cars
PSEASS - EJI
Eduardo JR Ilagan

car_repo.py — OOP repos for Cars + Maintenance (no sqlite3 here).
Aligned with ERD tables: cars, maintenance
UML links: UC-03 View Available Cars, UC-10/11 Record/Complete Maintenance,
           UC-13/14 Block/Unblock Car, UC-15 Check Maintenance Conflicts.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, List, Dict, Any, Tuple

from sql_repo import repo as _repo, SqlError

# ────────────────────────────────────────────────────────────────────────────────
# Errors (kept local to this module)
# ────────────────────────────────────────────────────────────────────────────────
class RepoError(Exception): ...
class DomainError(Exception): ...

# ────────────────────────────────────────────────────────────────────────────────
# Helpers
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

def _ranges_overlap(a1: date, a2: date, b1: date, b2: date) -> bool:
    # Overlap if: a1 < b2 and a2 > b1 (half-open logic)
    return a1 < b2 and a2 > b1

# ────────────────────────────────────────────────────────────────────────────────
# Domain classes (encapsulation)
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
    available_now: int  # 1 yes / 0 no
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
    type: str       # service / repair / WOF / etc
    cost: Optional[float]
    start_date: date
    end_date: Optional[date]
    notes: Optional[str]

    def active(self) -> bool:
        return self.end_date is None

    def overlaps(self, s: date, e: date) -> bool:
        m_end = self.end_date or date.max
        return _ranges_overlap(self.start_date, m_end, s, e)

# ────────────────────────────────────────────────────────────────────────────────
# Repositories
# ────────────────────────────────────────────────────────────────────────────────
class CarRepo:
    def __init__(self):
        self.sql = _repo()

    # Row mappers
    @staticmethod
    def _row_to_car(r: Dict[str, Any]) -> Car:
        return Car(
            id=r.get("car_id"), make=r["make"], model=r["model"], year=r["year"],
            color=r.get("color"), mileage=r.get("mileage"), daily_rate=r["daily_rate"],
            available_now=r["available_now"], min_days=r["min_rent_days"], max_days=r["max_rent_days"]
        )

    @staticmethod
    def _row_to_maint(r: Dict[str, Any]) -> Maint:
        sd = _parse_date(r["start_date"])
        ed = _parse_date(r["end_date"]) if r.get("end_date") else None
        return Maint(
            id=r.get("maint_id"), car_id=r["car_id"], type=r["type"], cost=r.get("cost"),
            start_date=sd, end_date=ed, notes=r.get("notes")
        )

    # Cars CRUD
    def get(self, car_id: int) -> Optional[Car]:
        r = self.sql.select_one("cars", where={"car_id__eq": car_id})
        return self._row_to_car(r) if r else None

    def list(self, **filters) -> List[Car]:
        where: Dict[str, Any] = {}
        if "make" in filters: where["make__like"] = f"%{filters['make']}%"
        if "model" in filters: where["model__like"] = f"%{filters['model']}%"
        if "year_min" in filters: where["year__gte"] = int(filters["year_min"])
        if "year_max" in filters: where["year__lte"] = int(filters["year_max"])
        if "available" in filters: where["available_now__eq"] = 1 if filters["available"] else 0
        rows = self.sql.select("cars", where=where, order=[("year","DESC"), ("make","ASC"), ("model","ASC")])
        return [self._row_to_car(r) for r in rows]

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
        if not car.id: raise RepoError("Car id required for update.")
        changes = {
            "make": car.make, "model": car.model, "year": car.year, "color": car.color,
            "mileage": car.mileage, "daily_rate": car.daily_rate, "available_now": car.available_now,
            "min_rent_days": car.min_days, "max_rent_days": car.max_days
        }
        return self.sql.update("cars", where={"car_id__eq": car.id}, changes=changes)

    def delete(self, car_id: int) -> int:
        return self.sql.delete("cars", where={"car_id__eq": car_id})

    # Maintenance
    def maint_open(self, car_id: int, type: str, start_date: str | date,
                   *, cost: Optional[float]=None, notes: Optional[str]=None) -> Maint:
        s = _parse_date(start_date)
        mid = self.sql.insert("maintenance", {
            "car_id": car_id, "type": type, "cost": cost, "start_date": s.isoformat(),
            "end_date": None, "notes": notes
        })
        return Maint(mid, car_id, type, cost, s, None, notes)

    def maint_close(self, maint_id: int, end_date: str | date | None = None, notes: Optional[str]=None) -> int:
        e = _parse_date(end_date) if end_date else date.today()
        changes: Dict[str, Any] = {"end_date": e.isoformat()}
        if notes is not None: changes["notes"] = notes
        return self.sql.update("maintenance", where={"maint_id__eq": maint_id}, changes=changes)

    def maint_active_for_car(self, car_id: int) -> List[Maint]:
        rows = self.sql.select("maintenance", where={"car_id__eq": car_id, "end_date__isnull": True})
        return [self._row_to_maint(r) for r in rows]

    def maint_overlaps(self, car_id: int, start_date: str | date, end_date: str | date) -> bool:
        s, e = _parse_date(start_date), _parse_date(end_date)
        # Any maint where maint.start < e AND (maint.end or distant future) > s
        rows = self.sql.select("maintenance", where={
            "car_id__eq": car_id,
            "start_date__lt": e.isoformat()
        })
        for r in rows:
            m = self._row_to_maint(r)
            if m.overlaps(s, e):
                return True
        return False
    
    # Get one maintenance record by id
    def maint_get(self, maint_id: int) -> Maint | None:
        r = self.sql.select_one("maintenance", where={"maint_id__eq": maint_id})
        return self._row_to_maint(r) if r else None

# List maintenance records (filterable)
    def maint_list(
        self,
        *,
        active_only: bool | None = None,   # True=open only, False=closed only, None=all
        car_id: int | None = None,
        sort: str = "start_desc",          # 'start_desc' | 'start_asc'
    ) -> list[Maint]:
        where: dict[str, object] = {}
        if car_id is not None:
            where["car_id__eq"] = car_id
        if active_only is True:
            where["end_date__isnull"] = True
        elif active_only is False:
            where["end_date__isnull"] = False

        order = [("start_date", "DESC" if sort.endswith("desc") else "ASC")]
        rows = self.sql.select("maintenance", where=where, order=order)
        return [self._row_to_maint(r) for r in rows]

    # Pretty label for display
    def maint_label(self, m: Maint) -> str:
        car = self.get(m.car_id)
        car_label = car.label() if car else f"car_id={m.car_id}"
        status = "OPEN" if m.active() else "CLOSED"
        end = m.end_date.isoformat() if m.end_date else "…"
        cost_txt = f"{(m.cost or 0):.2f}"
        return f"#{m.id} [{status}] {car_label} | {m.type} | {m.start_date.isoformat()} → {end} | cost={cost_txt}"


    # Availability (UC-03, UC-15 include)
    def available_in_range(self, start_date: str | date, end_date: str | date,
                           *, min_days: Optional[int]=None, max_days: Optional[int]=None) -> List[Car]:
        s, e = _parse_date(start_date), _parse_date(end_date)
        days = _days(s, e)
        rows = self.sql.select("cars", where={"available_now__eq": 1})
        cars = [self._row_to_car(r) for r in rows]

        # Filter by duration policy & conflicts (bookings + maintenance)
        from booking_repo import BookingRepo  
        bkr = BookingRepo()
        out: List[Car] = []
        for c in cars:
            # apply requested min/max filters if provided; otherwise the car's
            if min_days is not None and days < min_days: continue
            if max_days is not None and days > max_days: continue
            try:
                c.validate_days(days)
            except DomainError:
                continue
            if self.maint_overlaps(c.id, s, e):  # UC-15
                continue
            if bkr.car_has_overlap(c.id, s, e):  # conflict with approved bookings
                continue
            out.append(c)
        return out
