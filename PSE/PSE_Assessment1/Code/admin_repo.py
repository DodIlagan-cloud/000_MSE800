#!/usr/bin/env python3
"""
Assessment 1 - Car System - Dod's Cars
PSEASS - EJI
Eduardo JR Ilagan

admin_repo.py — Admin operations & menus.
Uses OOP repos: CarRepo, BookingRepo. Calls user_repo.users_admin_menu() for user admin.

Aligned with UML:
- UC-07 Manage Cars
- UC-08 Approve/Reject Booking
- UC-10/11 Record/Complete Maintenance
- UC-13/14 Block/Unblock Car (via maintenance windows)
- UC-15 Check Maintenance Conflicts (enforced on approval)
"""
from __future__ import annotations
from typing import Optional, Dict, Any, List
import datetime
import sql_repo as _sql
from sql_repo import repo as _repo, require_tables_configured as _require, SqlError, prompt_required_text, prompt_required_int, prompt_required_float
from car_repo import CarRepo, Car, DomainError as CarDomainError, RepoError as CarRepoError
from booking_repo import BookingRepo, DomainError as BkgDomainError, RepoError as BkgRepoError
from user_repo import UserRepo, DomainError as UserDomainError, RepoError as UserRepoError
import analytics_repo

# ────────────────────────────────────────────────────────────────────────────────
# Schema guard
# ────────────────────────────────────────────────────────────────────────────────
def ensure_schema():
    try:
        _require(["cars", "bookings", "booking_charges", "maintenance", "users"])
    except SqlError as e:
        raise RuntimeError(str(e))

# ────────────────────────────────────────────────────────────────────────────────
# SERVICES (non-interactive) — good for tests or other UIs
# ────────────────────────────────────────────────────────────────────────────────
# Cars
def car_add(*, make: str, model: str, year: int, daily_rate: float,
            color: str | None = None, mileage: int | None = None,
            available_now: int = 1, min_days: int = 1, max_days: int = 30) -> Car:
    c = Car(None, make, model, int(year), color, mileage, float(daily_rate),
            int(available_now), int(min_days), int(max_days))
    with _repo().conn:
        return CarRepo().create(c)

def car_update(car_id: int, **changes) -> int:
    cr = CarRepo()
    c = cr.get(car_id)
    if not c:
        raise CarRepoError("Car not found.")
    # Map known fields if present
    for fld in ("make", "model", "year", "color", "mileage", "daily_rate", "available_now", "min_days", "max_days"):
        if fld in changes and changes[fld] is not None:
            setattr(c, fld if fld != "min_days" else "min_days", changes[fld])
    with _repo().conn:
        return cr.save(c)

def car_delete(car_id: int) -> int:
    with _repo().conn:
        return CarRepo().delete(car_id)

def car_list(**filters) -> List[Car]:
    return CarRepo().list(**filters)

# Maintenance
def maint_open(*, car_id: int, type: str, start_date: str,
               cost: float | None = None, notes: str | None = None):
    with _repo().conn:
        return CarRepo().maint_open(car_id, type, start_date, cost=cost, notes=notes)

def maint_close(*, maint_id: int, end_date: str | None = None, notes: str | None = None) -> int:
    with _repo().conn:
        return CarRepo().maint_close(maint_id, end_date=end_date, notes=notes)

# Bookings approvals
def booking_approve(booking_id: int) -> int:
    with _repo().conn:
        return BookingRepo().approve(booking_id)

def booking_reject(booking_id: int, reason: str | None = None) -> int:
    with _repo().conn:
        return BookingRepo().reject(booking_id, reason)

def booking_list_pending():
    return BookingRepo().list_pending()

def _print_pending_with_details(br) -> tuple[bool, dict]:
    """
    List pending bookings with: Customer full name + Car year/make/model.
    Returns (has_any, context_cache_dict) so caller can decide next steps.
    """

    ID_W, CUST_W, CAR_W, DATES_W, TOTAL_W = 4, 24, 26, 26, 12

    def trim(s: str | None, w: int) -> str:
        s = "" if s is None else str(s)
        return s if len(s) <= w else (s[: max(0, w - 1)] + "…")

    row_fmt = (
        f" {{id:>{ID_W}}} | "
        f"{{cust:<{CUST_W}}} | "
        f"{{car:<{CAR_W}}} | "
        f"{{dates:<{DATES_W}}} | "
        f"{{total:>{TOTAL_W}}}"
    )
    sep = (
        "-" * (ID_W + 2) + "+" +
        "-" * (CUST_W + 2) + "+" +
        "-" * (CAR_W + 2) + "+" +
        "-" * (DATES_W + 2) + "+" +
        "-" * (TOTAL_W + 2)
    )
    pend = br.list_pending()
    if not pend:
        print("\nThere are no pending bookings to act on.\n")
        return False, {}

    ur = UserRepo()
    cr = CarRepo()
    users_cache = {}
    cars_cache = {}

    # Header
    print("\nPending bookings:")
    print(row_fmt.format(id="ID", cust="Customer", car="Car", dates="Dates", total="Total"))
    print(sep)

    # Rows
    for b in pend:
        u = users_cache.get(b.user_id) or ur.get_by_id(b.user_id); users_cache[b.user_id] = u
        c = cars_cache.get(b.car_id)  or cr.get(b.car_id);         cars_cache[b.car_id] = c

        cust  = trim(u.full_name if u else f"user {b.user_id}", CUST_W)
        car   = trim(f"{c.year} {c.make} {c.model}" if c else f"car {b.car_id}", CAR_W)
        dates = trim(f"{b.start_date}→{b.end_date} ({b.days}d)", DATES_W)
        total = f"${b.total_fee:,.2f}"

        print(row_fmt.format(id=b.id, cust=cust, car=car, dates=dates, total=total))

    print()
    return True, {"users": users_cache, "cars": cars_cache}

# Bookings on behalf of customer
def booking_create_on_behalf(*, customer_email: str, start_date: str, end_date: str, car_id: int, extras: list[dict] | None = None):
    """
    Create a PENDING booking for the specified customer (by email).
    Returns the created Booking object.
    """
    ur = UserRepo()
    u = ur.get_by_email(customer_email.strip().lower())
    if not u:
        raise UserRepoError("Customer not found.")
    # (Optional) enforce role:
    # if u.role != "customer": raise UserRepoError("Target user must be a customer.")
    with _repo().conn:
        return BookingRepo().create_pending(
            user_id=u.id, car_id=car_id, start_date=start_date, end_date=end_date, extras=extras
        )

# ────────────────────────────────────────────────────────────────────────────────
# SUBMENUS
# ────────────────────────────────────────────────────────────────────────────────
def admin_cars_menu():
    while True:
        print("\n========== Admin — Cars ==========")
        print(" 1) List cars")
        print(" 2) Add car")
        print(" 3) Edit car")
        print(" 4) Delete car")
        print(" 0) Back")
        print("==================================\n")
        ch = input("Choose: ").strip()
        try:
            if ch == "0":
                return
            elif ch == "1":
                _cars = car_list()
                if not _cars:
                    print("No cars.")
                else:
                    for c in _cars:
                        print(f" {c.id}: {c.label()} | ${c.daily_rate}/day | avail={c.available_now} | policy {c.min_days}-{c.max_days}")
            elif ch == "2":
                make  = prompt_required_text("Make")
                model = prompt_required_text("Model")
                year  = prompt_required_int("Year")
                rate  = prompt_required_float("Daily rate")
                min_d = prompt_required_int("Min days")
                max_d = prompt_required_int("Max days")
                color = prompt_required_text("Color") 
                mil_s = input("Mileage: ").strip()
                mileage = int(mil_s) if mil_s else None
                c = car_add(make=make, model=model, year=year, daily_rate=rate,
                            color=color, mileage=mileage, min_days=min_d, max_days=max_d)
                print(f"Created car id={c.id}: {c.label()}")
            elif ch == "3":
                cid = int(input("Car id: ").strip())
                print("Press Enter to keep a field unchanged.")
                make  = input("Make: ").strip() or None
                model = input("Model: ").strip() or None
                year  = input("Year: ").strip()
                year  = int(year) if year else None
                rate  = input("Daily rate: ").strip()
                rate  = float(rate) if rate else None
                min_d = input("Min days: ").strip()
                min_d = int(min_d) if min_d else None
                max_d = input("Max days: ").strip()
                max_d = int(max_d) if max_d else None
                color = input("Color: ").strip() or None
                mil_s = input("Mileage: ").strip()
                mileage = int(mil_s) if mil_s else None
                avail = input("Available now [0/1]: ").strip()
                avail = int(avail) if avail else None
                n = car_update(cid, make=make, model=model, year=year, daily_rate=rate,
                               min_days=min_d, max_days=max_d, color=color, mileage=mileage,
                               available_now=avail)
                print("Updated." if n else "No changes.")
            elif ch == "4":
                cid = int(input("Car id: ").strip())
                confirm = input(f"Type 'delete' to confirm deleting car {cid}: ").strip().lower()
                if confirm != "delete":
                    print("Cancelled.")
                else:
                    n = car_delete(cid)
                    print("Deleted." if n else "Car not found.")
            else:
                print("Choose a valid option.")
        except (ValueError, CarDomainError, CarRepoError) as ex:
            print(f"Error: {ex}")

def admin_approvals_menu():
    while True:
        print("\n===== Admin — Booking Approvals =====")
        pend = booking_list_pending()
        if not pend:
            print("No pending bookings.")
        else:
            for b in pend:
                print(f" {b.id}: user={b.user_id} car={b.car_id} {b.start_date}→{b.end_date} ({b.days}d) | ${b.total_fee:.2f}")
        print("-------------------------------------")
        print(" 1) Approve a booking")
        print(" 2) Reject a booking")
        print(" 0) Back")
        print("=====================================\n")
        ch = input("Choose: ").strip()
        try:
            if ch == "0":
                return
            bid = int(input("Booking id: ").strip()) if ch in ("1","2") else None
            if ch == "1":
                booking_approve(bid)
                print("Approved.")
            elif ch == "2":
                reason = input("Reason (optional): ").strip() or None
                booking_reject(bid, reason)
                print("Rejected.")
            else:
                print("Choose a valid option.")
        except (ValueError, BkgDomainError, BkgRepoError) as ex:
            print(f"Error: {ex}")

def admin_bookings_menu():
    br = BookingRepo()
    cr = CarRepo()
    ur = UserRepo()

    while True:
        print("\n===== Admin — Bookings =====")
        print(" 1) List pending")
        print(" 2) Approve a booking")
        print(" 3) Reject a booking")
        print(" 4) Create booking on behalf of customer")
        print(" 5) List all bookings")   
        print(" 0) Back")
        print("====================================\n")
        ch = input("Choose: ").strip()

        try:
            if ch == "0":
                return

            elif ch == "1":
                 _print_pending_with_details(br)
            elif ch == "2":
                has_any, _ = _print_pending_with_details(br)
                if not has_any:
                    continue
                bid = int(input("Booking id to approve: ").strip())
                with _repo().conn:
                    br.approve(bid)
                print("Approved.")

            elif ch == "3":
                has_any, _ = _print_pending_with_details(br)
                if not has_any:
                    continue
                bid = int(input("Booking id to reject: ").strip())
                reason = input("Reason (optional): ").strip() or None
                with _repo().conn:
                    br.reject(bid, reason)
                print("Rejected.")

            elif ch == "4":
                # --- Create on behalf flow ---
                cust_email = input("Customer email: ").strip().lower()
                u = ur.get_by_email(cust_email)
                if not u:
                    print("Customer not found."); continue
                # if u.role != "customer": print("User is not a customer."); continue

                start = input("Start date (YYYY-MM-DD): ").strip()
                end   = input("End date   (YYYY-MM-DD): ").strip()

                # show available cars for the range
                cars = cr.available_in_range(start, end)
                if not cars:
                    print("No cars available for that range."); continue
                for c in cars:
                    print(f" {c.id}: {c.label()} | ${c.daily_rate}/day")

                car_id = int(input("Choose car id: ").strip())

                with _repo().conn:
                    b = br.create_pending(user_id=u.id, car_id=car_id, start_date=start, end_date=end, extras=None)
                print(f"Booking created (pending): id={b.id}, customer={u.email}, car={b.car_id}, days={b.days}, total=${b.total_fee:.2f}")
            elif ch == "5":                    
                import booking_repo
                booking_repo.list_all_bookings_cli()
            else:
                print("Choose a valid option.")

        except (ValueError, 
                CarDomainError, CarRepoError, 
                BkgDomainError, BkgRepoError, 
                UserRepoError, UserDomainError) as ex:
            print(f"Error: {ex}")


def admin_maintenance_menu():
    while True:
        print("\n========= Admin — Maintenance =========")
        print(" 1) Open maintenance")
        print(" 2) Close maintenance")
        print(" 3) Manage maintenance") 
        print(" 4) List all maintenance")
        print(" 0) Back")
        print("======================================\n")
        ch = input("Choose: ").strip()
        try:
            if ch == "0":
                return
            if ch == "1":
                car_id = int(input("Car id: ").strip())
                type_  = input("Type (service/repair/WOF): ").strip()
                start  = input("Start date (YYYY-MM-DD): ").strip()
                notes  = input("Notes (optional): ").strip() or None
                cost_s = input("Cost (optional): ").strip()
                cost   = float(cost_s) if cost_s else None
                maint_open(car_id=car_id, type=type_, start_date=start, cost=cost, notes=notes)
                print("Maintenance opened.")
            elif ch == "2":
                mid   = int(input("Maintenance id: ").strip())
                end   = input("End date (YYYY-MM-DD) [today]: ").strip() or None
                notes = input("Notes (optional): ").strip() or None
                n = maint_close(maint_id=mid, end_date=end, notes=notes)
                print("Maintenance closed." if n else "No changes.")
            elif ch == "3":
                admin_maintenance_list_menu()
            elif ch == "4":
                admin_list_all_maintenance_cli()
            else:
                print("Choose a valid option.")
        except (ValueError, CarDomainError, CarRepoError) as ex:
            print(f"Error: {ex}")

def admin_maintenance_list_menu():
    cr = CarRepo()
    while True:
        print("\n===== Admin — Maintenance List =====")
        print(" 1) Show OPEN items")
        print(" 2) Show ALL items")
        print(" 3) Show by CAR id")
        print(" 0) Back")
        print("===================================\n")
        ch = input("Choose: ").strip()

        try:
            if ch == "0":
                return
            elif ch == "1":
                items = cr.maint_list(active_only=True)
            elif ch == "2":
                items = cr.maint_list(active_only=None)
            elif ch == "3":
                cid = int(input("Car id: ").strip())
                items = cr.maint_list(car_id=cid, active_only=None)
            else:
                print("Choose a valid option.")
                continue

            if not items:
                print("No maintenance records.")
            else:
                print()
                for m in items:
                    print(" ", cr.maint_label(m))

            # Quick action: close by id
            print("\nActions:  C) Close a maintenance  |  Enter) Back")
            act = input("Choose: ").strip().lower()
            if act == "c":
                mid = int(input("Maintenance id to close: ").strip())
                end = input("End date (YYYY-MM-DD) [today]: ").strip() or None
                with _repo().conn:
                    n = cr.maint_close(mid, end_date=end)
                print("Closed." if n else "No changes.")
            else:
                # Back to list menu top
                continue

        except (ValueError, CarDomainError, CarRepoError) as ex:
            print(f"Error: {ex}")

def _pp_maintenance(rows):
    print("\nAll Maintenance")
    if not rows:
        print("  (no maintenance records)\n"); return
    hdr = "  {:>5}  {:<22}  {:<10}  {:>8}  {:<10}  {:<10}  {:<24}"
    print(hdr.format("ID","Car","Type","Cost","Start","End","Notes"))
    print("  " + "-"*105)
    line = "  {:>5}  {:<22}  {:<10}  ${:>7.2f}  {:<10}  {:<10}  {:<24}"
    for r in rows:
        car = f"{r.get('car_year','')} {r.get('car_make','')} {r.get('car_model','')}"
        print(line.format(
            int(r["maint_id"]),
            car[:22],
            (r.get("type",""))[:10],
            float(r.get("cost",0.0)),
            (r.get("start_date",""))[:10],
            (r.get("end_date","") or "")[:10],
            (r.get("notes","") or "")[:24],
        ))
    print()

def admin_list_all_maintenance_cli():
    filt = input("\nFilter by status [all/open/closed] (Enter=all): ").strip().lower()
    status = filt if filt in ("open","closed") else None
    rows = _sql.list_all_maintenance(status=status)
    _pp_maintenance(rows)

# ────────────────────────────────────────────────────────────────────────────────
# Admin — Analytics Dashboard
# ────────────────────────────────────────────────────────────────────────────────
def admin_analytics_menu():
    while True:
        print("\n===== Analytics Dashboard =====")
        print(" 1) Top Users (by revenue, year)")
        print(" 2) Top Car Revenue (year)")
        print(" 3) Cars with Highest Maintenance Cost (year)")
        print(" 0) Back")
        choice = input("Choose: ").strip()

        if choice in ("1","2","3"):
        # Year (defaults to current if blank)
            y_in = input("Enter year (YYYY) [default: current]: ").strip()
            if not y_in:
                year = datetime.date.today().year
            else:
                try:
                    year = int(y_in)
                except ValueError:
                    print("Please enter a valid year (e.g., 2025).")
                    continue

            # Row limit (defaults to 5)
            lim_in = input("How many rows? [5]: ").strip()
            limit = 5
            if lim_in:
                try:
                    limit = max(1, int(lim_in))
                except ValueError:
                    print("Using default: 5")


        if choice == "0":
            return
        if choice == "1":
            # Top Users by revenue for the year
            analytics_repo.print_top_users(year, limit)
        elif choice == "2":
            # Top revenue cars for the year
            analytics_repo.print_top_car_revenue(year, limit)
        elif choice == "3":
            # Highest maintenance cost cars for the year
            analytics_repo.print_highest_maint_cost(year, limit)
        else:
            print("Please choose a valid option.")

