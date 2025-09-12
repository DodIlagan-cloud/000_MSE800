#!/usr/bin/env python3
"""
analytics_repo.py — Dod's Cars Analytics (formatting only)
All database access lives in sql_repo.*
"""

from __future__ import annotations
from typing import Optional, List, Dict
from pathlib import Path

import sql_repo


# ────────────────────────────────────────────────────────────────────────────────
# Pretty-print helpers (no DB here)
# ────────────────────────────────────────────────────────────────────────────────
def _print_table(headers: list[str], rows: list[tuple], widths: list[int]) -> None:
    fmt = " | ".join([f"{{:{w}}}" for w in widths])
    sep = "-+-".join(["-" * w for w in widths])
    print(fmt.format(*headers))
    print(sep)
    for r in rows:
        trimmed = []
        for v, w in zip(r, widths):
            s = "" if v is None else str(v)
            trimmed.append(s if len(s) <= w else s[: max(0, w - 1)] + "…")
        print(fmt.format(*trimmed))
    print()


# ────────────────────────────────────────────────────────────────────────────────
# Formatting wrappers around sql_repo analytics
# ────────────────────────────────────────────────────────────────────────────────
def print_most_rented_cars(limit: int = 10, start: Optional[str] = None, end: Optional[str] = None) -> None:
    data = sql_repo.analytics_most_rented_cars(start=start, end=end, limit=limit)
    print(f"Most Rented Cars (top {limit})")
    if not data:
        print("  (no data)\n"); return
    rows = [(f"{r['year']} {r['make']} {r['model']}", r['rentals'], r['days']) for r in data]
    _print_table(["Car", "Rentals", "Days"], rows, [28, 8, 6])

def print_monthly_revenue(year: Optional[int] = None, start: Optional[str] = None, end: Optional[str] = None) -> None:
    data = sql_repo.analytics_monthly_revenue(year=year, start=start, end=end)
    title = "Monthly Revenue" + (f" — {year}" if year is not None else "")
    print(title)
    if not data:
        print("  (no data)\n"); return
    rows = [(r["ym"], f"${r['revenue']:.2f}", r["bookings"]) for r in data]
    _print_table(["Month", "Revenue", "Bookings"], rows, [8, 12, 9])

def print_avg_rental_duration(start: Optional[str] = None, end: Optional[str] = None) -> None:
    v = sql_repo.analytics_avg_rental_duration(start=start, end=end)
    print("Average Rental Duration")
    print(f"  {v:.2f} days\n" if v is not None else "  (no data)\n")

def print_top_users(year: int, limit: int = 5) -> None:
    rows = sql_repo.analytics_top_users(year, limit)
    print(f"Top Users by Revenue — {year} (top {limit})")
    if not rows:
        print("  No approved bookings for this year.\n"); return
    print("  {:>3}  {:<22} {:<24} {:>7}  {:>12}".format("#", "Name", "Email", "Rentals", "Revenue"))
    print("  " + "-" * 76)
    for i, r in enumerate(rows, 1):
        print("  {:>3}  {:<22} {:<24} {:>7}  ${:>11.2f}".format(
            i,
            (r.get("full_name",""))[:22],
            (r.get("email",""))[:24],
            int(r.get("rentals",0)),
            float(r.get("revenue",0.0))
        ))
    print()

def print_top_car_revenue(year: int, limit: int = 5) -> None:
    rows = sql_repo.analytics_top_car_revenue(year, limit)
    print(f"Top Car Revenue — {year} (top {limit})")
    if not rows:
        print("  No approved bookings for this year.\n"); return
    print("  {:>3}  {:<24} {:>7}  {:>12}".format("#","Car","Rentals","Revenue"))
    print("  " + "-" * 54)
    for i, r in enumerate(rows, 1):
        car = f"{r.get('year','')} {r.get('make','')} {r.get('model','')}"
        print("  {:>3}  {:<24} {:>7}  ${:>11.2f}".format(
            i, car[:24], int(r.get("rentals",0)), float(r.get("revenue",0.0))
        ))
    print()

def print_highest_maint_cost(year: int, limit: int = 5) -> None:
    rows = sql_repo.analytics_highest_maint_cost(year, limit)
    print(f"Cars with Highest Maintenance Cost — {year} (top {limit})")
    if not rows:
        print("  No maintenance records for this year.\n"); return
    print("  {:>3}  {:<24} {:>5}  {:>12}  {:>10}".format("#","Car","Jobs","Total Cost","Avg Cost"))
    print("  " + "-" * 64)
    for i, r in enumerate(rows, 1):
        car = f"{r.get('year','')} {r.get('make','')} {r.get('model','')}"
        print("  {:>3}  {:<24} {:>5}  ${:>11.2f}  ${:>9.2f}".format(
            i, car[:24], int(r.get("jobs",0)),
            float(r.get("total_cost",0.0)), float(r.get("avg_cost",0.0))
        ))
    print()

def print_maintenance_summary(start: Optional[str] = None, end: Optional[str] = None) -> None:
    rows = sql_repo.analytics_maintenance_summary(start=start, end=end)
    print("Maintenance Summary (cost & downtime)")
    if not rows:
        print("  (no data)\n"); return
    data = [(f"{r['year']} {r['make']} {r['model']}", f"${r['maint_cost']:.2f}", r['downtime_days']) for r in rows]
    _print_table(["Car", "Maint Cost", "Downtime (d)"], data, [28, 12, 12])


# ────────────────────────────────────────────────────────────────────────────────
# Composite report (still formatting only)
# ────────────────────────────────────────────────────────────────────────────────
def print_report(*, start: Optional[str], end: Optional[str], year: Optional[int]) -> None:
    print("\n=== Dod's Cars — Analytics Report ===")
    if start or end:
        print(f"Window: {start or '…'}  to  {end or '…'}")
    if year is not None:
        print(f"Year: {year}")
    print("-------------------------------------\n")

    print_most_rented_cars(limit=10, start=start, end=end)
    print_monthly_revenue(year=year, start=start, end=end)
    print_avg_rental_duration(start=start, end=end)
    print_maintenance_summary(start=start, end=end)
    print("=== End of report ===\n")


# ────────────────────────────────────────────────────────────────────────────────
# CLI (optional)
# ────────────────────────────────────────────────────────────────────────────────
def parse_args():
    import argparse
    p = argparse.ArgumentParser(description="Dod's Cars — Analytics (formatting only)")
    p.add_argument("--db", help="Path to SQLite DB file (overrides default)")
    p.add_argument("--start", help="Filter from date (YYYY-MM-DD)")
    p.add_argument("--end", help="Filter up to date (YYYY-MM-DD)")
    p.add_argument("--year", type=int, help="Year for monthly/annual reports (e.g., 2025)")
    return p.parse_args()

def main():
    args = parse_args()

    # Configure DB once (use app defaults if --db not provided)
    if args.db:
        sql_repo.configure(args.db)
    else:
        # Respect your existing default path logic in sql_repo (e.g., AppData)
        sql_repo.configure(sql_repo.get_args(description="Analytics").db)

    # Always ensure required tables exist
    sql_repo.require_tables_configured(["users","cars","bookings","booking_charges","maintenance"])

    # Run composite report
    print_report(start=args.start, end=args.end, year=args.year)

if __name__ == "__main__":
    main()
