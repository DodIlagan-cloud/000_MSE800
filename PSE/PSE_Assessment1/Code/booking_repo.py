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
from typing import Optional, List, Dict, Any

from sql_repo import repo as _repo, SqlError, ranges_overlap
from base_repo import BookingFactoryABC # <-- ABC factory


# Local errors
class RepoError(Exception): ...
class DomainError(Exception): ...

def _parse_date(d: str | date) -> date:
    if isinstance(d, date): return d
    try:
        return datetime.strptime(d, "%Y-%m-%d").date()
    except Exception:
        raise DomainError("Dates must be 'YYYY-MM-DD'.")

def _days(start: date, end: date) -> int:
    n = (end - start).days
    if n <= 0: raise DomainError("end_date must be after start_date.")
    return n


# ────────────────────────────────────────────────────────────────────────────────
# Domain classes
# ────────────────────────────────────────────────────────────────────────────────
@dataclass
class Charge:
    id: Optional[int]
    booking_id: int
    code: str
    amount: float

@dataclass
class Booking:
    id: Optional[int]
    user_id: int
    car_id: int
    start_date: date
    end_date: date
    days: int
    total_fee: float
    status: str       # pending | approved | rejected
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, r: dict) -> "Booking":
        sd = datetime.strptime(r["start_date"], "%Y-%m-%d").date()
        ed = datetime.strptime(r["end_date"], "%Y-%m-%d").date()
        return cls(
            id=r.get("booking_id"), user_id=r["user_id"], car_id=r["car_id"],
            start_date=sd, end_date=ed, days=r["rental_days"],
            total_fee=r["total_fee"], status=r["status"], created_at=r.get("created_at")
        )
    def overlaps(self, s: date, e: date) -> bool:
        """Return True if this booking overlaps the [s, e) interval."""
        return ranges_overlap(self.start_date, self.end_date, s, e)

# ────────────────────────────────────────────────────────────────────────────────
# ABC class additional for Factory Design Pattern
# ────────────────────────────────────────────────────────────────────────────────
class _DefaultBookingFactory(BookingFactoryABC):
    def booking_from_row(self, r: Dict[str, Any]):
        sd = _parse_date(r["start_date"]); ed = _parse_date(r["end_date"])
        return Booking(
            id=r.get("booking_id"), user_id=r["user_id"], car_id=r["car_id"],
            start_date=sd, end_date=ed, days=r["rental_days"],
            total_fee=r["total_fee"], status=r["status"], created_at=r.get("created_at")
        )
    def charge_from_row(self, r: Dict[str, Any]):
        return Charge(id=r.get("charge_id"), booking_id=r["booking_id"], code=r["code"], amount=r["amount"])

# ────────────────────────────────────────────────────────────────────────────────
# Repo
# ────────────────────────────────────────────────────────────────────────────────
class BookingRepo:
    """
    Booking repository (no raw sqlite3 here).
    - UC-04: create pending bookings
    - UC-05: list bookings per user
    - UC-06: calculate fees (included inside create/recalc)
    - UC-08: approve/reject with conflict enforcement
    - UC-15: maintenance/booking overlap checks (enforced at approve time)
    """

    def __init__(self, factory: BookingFactoryABC | None = None):
        self.sql = _repo()
        self._f: BookingFactoryABC = factory or _DefaultBookingFactory()

    # ──────────────────────────────────────────────────────────────────────
    # Queries  (UC-05)
    # ──────────────────────────────────────────────────────────────────────
    def get(self, booking_id: int) -> Optional[Booking]:
        r = self.sql.select_one("bookings", where={"booking_id__eq": booking_id})
        return self._f.booking_from_row(r) if r else None

    def list_by_user(self, user_id: int) -> List[Booking]:
        rows = self.sql.select(
            "bookings",
            where={"user_id__eq": user_id},
            order=[("created_at", "DESC")]
        )
        return [self._f.booking_from_row(r) for r in rows]

    def list_pending(self) -> List[Booking]:
        rows = self.sql.select(
            "bookings",
            where={"status__eq": "pending"},
            order=[("created_at", "ASC")]
        )
        return [self._f.booking_from_row(r) for r in rows]

    # ──────────────────────────────────────────────────────────────────────
    # Conflict checks (UC-15 include)
    # ──────────────────────────────────────────────────────────────────────
    def car_has_overlap(self, car_id: int, s: str | "date", e: str | "date") -> bool:
        """
        Return True if there exists an APPROVED booking for the same car that overlaps [s, e).
        Note: pending bookings do not block availability; conflict enforced on approval.
        """
        s_d, e_d = _parse_date(s), _parse_date(e)
        rows = self.sql.select("bookings", where={
            "car_id__eq": car_id,
            "status__eq": "approved",
            "start_date__lt": e_d.isoformat(),    # pre-filter; exact overlap via entity method
        })
        for r in rows:
            b = self._f.booking_from_row(r)
            if b.overlaps(s_d, e_d):
                return True
        return False

    # ──────────────────────────────────────────────────────────────────────
    # Fee calculation (UC-06 include)
    # ──────────────────────────────────────────────────────────────────────
    def _calc_fee(self, car_daily_rate: float, days: int, extras: List[Charge] | None) -> float:
        total = float(car_daily_rate) * days
        if extras:
            total += sum(float(c.amount) for c in extras)
        return round(total, 2)

    # ──────────────────────────────────────────────────────────────────────
    # Create pending booking (UC-04)
    # ──────────────────────────────────────────────────────────────────────
    def create_pending(
        self,
        user_id: int,
        car_id: int,
        start_date: str | "date",
        end_date: str | "date",
        extras: List[Dict[str, Any]] | None = None
    ) -> Booking:
        from car_repo import CarRepo  # lazy import to avoid cycle
        car = CarRepo().get(car_id)
        if not car:
            raise RepoError("Car not found.")

        s, e = _parse_date(start_date), _parse_date(end_date)
        days = _days(s, e)
        car.validate_days(days)  # car policy (min/max days)

        # Policy: conflicts (maintenance/approved bookings) are enforced on APPROVE (UC-15),
        # so creation can capture demand even if approval later fails.
        total = self._calc_fee(car.daily_rate, days, None)

        bid = self.sql.insert("bookings", {
            "user_id": user_id, "car_id": car_id,
            "start_date": s.isoformat(), "end_date": e.isoformat(),
            "rental_days": days, "total_fee": total, "status": "pending"
        })

        # Optional extras (still pending)
        if extras:
            for ex in extras:
                self.sql.insert("booking_charges", {
                    "booking_id": bid, "code": ex["code"], "amount": ex["amount"]
                })
            charges = self.charges_for(bid)
            total = self._calc_fee(car.daily_rate, days, charges)
            self.sql.update("bookings", where={"booking_id__eq": bid}, changes={"total_fee": total})

        return self.get(bid)

    # ──────────────────────────────────────────────────────────────────────
    # Charges (UC-06 include)
    # ──────────────────────────────────────────────────────────────────────
    def charges_for(self, booking_id: int) -> List[Charge]:
        rows = self.sql.select("booking_charges", where={"booking_id__eq": booking_id})
        return [self._f.charge_from_row(r) for r in rows]

    def add_charge(self, booking_id: int, code: str, amount: float) -> Charge:
        cid = self.sql.insert("booking_charges", {"booking_id": booking_id, "code": code, "amount": amount})
        return self._f.charge_from_row({"charge_id": cid, "booking_id": booking_id, "code": code, "amount": amount})

    def recalc(self, booking_id: int) -> float:
        """
        Recalculate total fee = daily_rate * days + sum(extras).
        Useful if extras change after creation.
        """
        b = self.get(booking_id)
        if not b:
            raise RepoError("Booking not found.")
        from car_repo import CarRepo
        car = CarRepo().get(b.car_id)
        if not car:
            raise RepoError("Car not found.")
        charges = self.charges_for(booking_id)
        total = self._calc_fee(car.daily_rate, b.days, charges)
        self.sql.update("bookings", where={"booking_id__eq": booking_id}, changes={"total_fee": total})
        return total

    # ──────────────────────────────────────────────────────────────────────
    # Status transitions (UC-08) — enforces UC-15 conflicts here
    # ──────────────────────────────────────────────────────────────────────
    def approve(self, booking_id: int) -> int:
        """
        Approve a pending booking.
        Enforces:
          - No overlap with active maintenance (CarRepo.maint_overlaps) [UC-15]
          - No overlap with existing APPROVED bookings [UC-15]
        """
        b = self.get(booking_id)
        if not b:
            raise RepoError("Booking not found.")
        if b.status != "pending":
            raise DomainError("Only pending bookings can be approved.")

        from car_repo import CarRepo
        cr = CarRepo()

        # Maintenance conflicts
        if cr.maint_overlaps(b.car_id, b.start_date, b.end_date):
            raise DomainError("Booking overlaps an active maintenance window.")

        # Approved bookings conflict
        if self.car_has_overlap(b.car_id, b.start_date, b.end_date):
            raise DomainError("Booking overlaps an existing approved booking.")

        return self.sql.update("bookings", where={"booking_id__eq": booking_id}, changes={"status": "approved"})

    def reject(self, booking_id: int, reason: Optional[str] = None) -> int:
        """
        Reject a pending booking (reason optional; log elsewhere if needed).
        """
        b = self.get(booking_id)
        if not b:
            raise RepoError("Booking not found.")
        if b.status != "pending":
            raise DomainError("Only pending bookings can be rejected.")
        return self.sql.update("bookings", where={"booking_id__eq": booking_id}, changes={"status": "rejected"})

# ────────────────────────────────────────────────────────────────────────────────
# Admin: List All Bookings (formatting only)
# ────────────────────────────────────────────────────────────────────────────────
import sql_repo

def _pp_bookings(rows):
    # Header
    print("\nAll Bookings")
    if not rows:
        print("  (no bookings found)\n"); return
    hdr = "  {:>5}  {:<22}  {:<22}  {:<22}  {:>5}  {:>10}  {:<9}"
    print(hdr.format("ID","Customer","Email","Car","Days","Total","Status"))
    print("  " + "-"*105)
    line = "  {:>5}  {:<22}  {:<22}  {:<22}  {:>5}  ${:>9.2f}  {:<9}"
    for r in rows:
        car = f"{r.get('car_year','')} {r.get('car_make','')} {r.get('car_model','')}"
        print(line.format(
            int(r["booking_id"]),
            (r.get("customer_name",""))[:22],
            (r.get("customer_email",""))[:22],
            car[:22],
            int(r.get("rental_days",0)),
            float(r.get("total_fee",0.0)),
            (r.get("status",""))[:9],
        ))
    print()

def list_all_bookings_cli():
    filt = input("\nFilter by status [all/pending/approved/rejected] (Enter=all): ").strip().lower()
    status = filt if filt in ("pending","approved","rejected") else None
    rows = sql_repo.list_all_bookings(status=status)
    _pp_bookings(rows)
