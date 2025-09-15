#!/usr/bin/env python3
"""
Assessment 1 - Car System - Dod's Cars
PSEASS - EJI
Eduardo JR Ilagan

customer_repo.py — Customer-facing services & menus (no sqlite3 here).
Aligned with UML:
- UC-03 View Available Cars
- UC-04 Create Booking
- UC-05 View Booking Status
(UC-06 Calculate Fees is handled inside BookingRepo when creating/recalc.)

All DB work goes through sql_repo + OOP repos (CarRepo, BookingRepo).
"""

from __future__ import annotations
from typing import Optional, List, Dict, Any

from sql_repo import repo as _repo, require_tables_configured as _require, SqlError, prompt_required_date
from car_repo import CarRepo, Car, DomainError as CarDomainError, RepoError as CarRepoError
from booking_repo import BookingRepo, Booking, DomainError as BkgDomainError, RepoError as BkgRepoError

# ────────────────────────────────────────────────────────────────────────────────
# Schema guard
# ────────────────────────────────────────────────────────────────────────────────
def ensure_schema():
    try:
        _require(["users", "cars", "bookings", "booking_charges", "maintenance"])
    except SqlError as e:
        raise RuntimeError(str(e))

# ────────────────────────────────────────────────────────────────────────────────
# SERVICES (non-interactive) — call these from tests or any UI
# ────────────────────────────────────────────────────────────────────────────────
def available_cars(start_date: str, end_date: str,
                   *, min_days: int | None = None, max_days: int | None = None) -> List[Car]:
    """UC-03: list cars that are available and policy-compliant for the range."""
    return CarRepo().available_in_range(start_date, end_date, min_days=min_days, max_days=max_days)

def create_booking(user_id: int, car_id: int, start_date: str, end_date: str,
                   extras: List[Dict[str, Any]] | None = None) -> Booking:
    """UC-04: create a pending booking; fees calculated in repo."""
    with _repo().conn:
        return BookingRepo().create_pending(user_id=user_id, car_id=car_id,
                                            start_date=start_date, end_date=end_date, extras=extras)

def my_bookings(user_id: int) -> List[Booking]:
    """UC-05: list bookings for this user."""
    return BookingRepo().list_by_user(user_id)

# (Optional) You can add a cancel_pending(...) later if the business rules allow.

# ────────────────────────────────────────────────────────────────────────────────
# INTERACTIVE FLOWS (small, console-based; keep main menu thin)
# ────────────────────────────────────────────────────────────────────────────────
def cust_view_available():
    """Prompt for a date range and display available cars (UC-03)."""
    s = input("Start date (YYYY-MM-DD): ").strip()
    e = input("End date   (YYYY-MM-DD): ").strip()
    try:
        cars = available_cars(s, e)
        if not cars:
            print("No cars available for that range.")
            return
        print("\nAvailable cars:")
        for c in cars:
            print(f" {c.id}: {c.label()} | ${c.daily_rate}/day | policy {c.min_days}-{c.max_days} days")
    except (CarDomainError, CarRepoError) as ex:
        print(f"Error: {ex}")

def cust_create_booking(user):
    """Create a pending booking for the logged-in user (UC-04)."""
    s = prompt_required_date("Start date")
    e = prompt_required_date("End date")
    try:
        cars = available_cars(s, e)
        if not cars:
            print("No cars available for that range."); return
        for c in cars:
            print(f" {c.id}: {c.label()} | ${c.daily_rate}/day")
        car_id = int(input("Choose car id: ").strip())
        b = create_booking(user_id=user.id, car_id=car_id, start_date=s, end_date=e, extras=None)
        print(f"Booking created (pending): id={b.id}, days={b.days}, total=${b.total_fee:.2f}")
    except (ValueError, CarDomainError, CarRepoError, BkgDomainError, BkgRepoError) as ex:
        print(f"Error: {ex}")

def cust_my_bookings(user):
    """Show all bookings for the logged-in user (UC-05)."""
    try:
        bks = my_bookings(user.id)
    except BkgRepoError as ex:
        print(f"Error: {ex}")
        return
    if not bks:
        print("No bookings.")
        return
    print("\nMy bookings:")
    for b in bks:
        print(f" {b.id}: car={b.car_id} {b.start_date}→{b.end_date} ({b.days}d) | ${b.total_fee:.2f} | {b.status}")
