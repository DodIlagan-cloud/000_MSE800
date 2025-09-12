#!/usr/bin/env python3
"""
booking_repo.py — OOP repo for Bookings (+ Charges). No sqlite3 here.
Aligned with ERD tables: bookings, booking_charges
UML links: UC-04 Create Booking, UC-06 Calculate Fees (include),
           UC-08 Approve/Reject Booking, UC-15 Check Maintenance Conflicts (include).
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, List, Dict, Any

from sql_repo import repo as _repo
from sql_repo import SqlError

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

def _ranges_overlap(a1: date, a2: date, b1: date, b2: date) -> bool:
    return a1 < b2 and a2 > b1

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

    def overlaps(self, s: date, e: date) -> bool:
        return _ranges_overlap(self.start_date, self.end_date, s, e)

# ────────────────────────────────────────────────────────────────────────────────
# Repo
# ────────────────────────────────────────────────────────────────────────────────
class BookingRepo:
    def __init__(self):
        self.sql = _repo()

    # Mappers
    @staticmethod
    def _row_to_booking(r: Dict[str, Any]) -> Booking:
        sd = _parse_date(r["start_date"]); ed = _parse_date(r["end_date"])
        return Booking(
            id=r.get("booking_id"), user_id=r["user_id"], car_id=r["car_id"],
            start_date=sd, end_date=ed, days=r["rental_days"],
            total_fee=r["total_fee"], status=r["status"], created_at=r.get("created_at")
        )

    @staticmethod
    def _row_to_charge(r: Dict[str, Any]) -> Charge:
        return Charge(id=r.get("charge_id"), booking_id=r["booking_id"], code=r["code"], amount=r["amount"])

    # Queries
    def get(self, booking_id: int) -> Optional[Booking]:
        r = self.sql.select_one("bookings", where={"booking_id__eq": booking_id})
        return self._row_to_booking(r) if r else None

    def list_by_user(self, user_id: int) -> List[Booking]:
        rows = self.sql.select("bookings", where={"user_id__eq": user_id}, order=[("created_at","DESC")])
        return [self._row_to_booking(r) for r in rows]

    def list_pending(self) -> List[Booking]:
        rows = self.sql.select("bookings", where={"status__eq": "pending"}, order=[("created_at","ASC")])
        return [self._row_to_booking(r) for r in rows]

    # Conflict checks (UC-15)
    def car_has_overlap(self, car_id: int, s: date | str, e: date | str) -> bool:
        s, e = _parse_date(s), _parse_date(e)
        # any approved booking where start < e and end > s
        rows = self.sql.select("bookings", where={
            "car_id__eq": car_id,
            "status__eq": "approved",
            "start_date__lt": e.isoformat()
        })
        for r in rows:
            b = self._row_to_booking(r)
            if b.overlaps(s, e):
                return True
        return False

    # UC-06 Calculate fees (simple: daily_rate * days + sum(extras))
    def _calc_fee(self, car_daily_rate: float, days: int, extras: List[Charge] | None) -> float:
        total = float(car_daily_rate) * days
        if extras:
            total += sum(float(c.amount) for c in extras)
        return round(total, 2)

    # Create pending booking (UC-04)
    def create_pending(self, *, user_id: int, car_id: int, start_date: str | date, end_date: str | date,
                       extras: List[Dict[str, Any]] | None = None) -> Booking:
        from car_repo import CarRepo  # lazy import to avoid cycle
        car = CarRepo().get(car_id)
        if not car:
            raise RepoError("Car not found.")

        s, e = _parse_date(start_date), _parse_date(end_date)
        days = _days(s, e)
        car.validate_days(days)

        # Conflicts with maintenance or approved bookings are only enforced on approve;
        # you can optionally enforce them here by importing CarRepo.maint_overlaps()
        total = self._calc_fee(car.daily_rate, days, None)

        bid = self.sql.insert("bookings", {
            "user_id": user_id, "car_id": car_id,
            "start_date": s.isoformat(), "end_date": e.isoformat(),
            "rental_days": days, "total_fee": total, "status": "pending"
        })

        # Add extras if any (still pending)
        if extras:
            for ex in extras:
                self.sql.insert("booking_charges", {"booking_id": bid, "code": ex["code"], "amount": ex["amount"]})
            # Recalc total with extras
            charges = self.charges_for(bid)
            total = self._calc_fee(car.daily_rate, days, charges)
            self.sql.update("bookings", where={"booking_id__eq": bid}, changes={"total_fee": total})

        return self.get(bid)

    # Charges
    def charges_for(self, booking_id: int) -> List[Charge]:
        rows = self.sql.select("booking_charges", where={"booking_id__eq": booking_id})
        return [self._row_to_charge(r) for r in rows]

    def add_charge(self, booking_id: int, code: str, amount: float) -> Charge:
        cid = self.sql.insert("booking_charges", {"booking_id": booking_id, "code": code, "amount": amount})
        return self._row_to_charge({"charge_id": cid, "booking_id": booking_id, "code": code, "amount": amount})

    def recalc(self, booking_id: int) -> float:
        b = self.get(booking_id)
        if not b: raise RepoError("Booking not found.")
        from car_repo import CarRepo
        car = CarRepo().get(b.car_id)
        charges = self.charges_for(booking_id)
        total = self._calc_fee(car.daily_rate, b.days, charges)
        self.sql.update("bookings", where={"booking_id__eq": booking_id}, changes={"total_fee": total})
        return total

    # Status transitions (UC-08)
    def approve(self, booking_id: int) -> int:
        b = self.get(booking_id)
        if not b: raise RepoError("Booking not found.")
        if b.status != "pending": raise DomainError("Only pending bookings can be approved.")

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
        b = self.get(booking_id)
        if not b: raise RepoError("Booking not found.")
        if b.status != "pending": raise DomainError("Only pending bookings can be rejected.")
        # Optionally log 'reason' somewhere (separate table / audit)
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
