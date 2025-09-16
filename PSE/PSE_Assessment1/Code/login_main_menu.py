#!/usr/bin/env python3
"""
Assessment 1 - Car System - Dod's Cars
PSEASS - EJI
Eduardo JR Ilagan

Dod's Cars — Login + Main Menu
- All SQL lives in repos (user_repo, car_repo, booking_repo, etc.)
- Admin menu includes Users CRUD and reset password
- DB bootstrap/seed via sql_repo.autoinit(...)
- OO flows via repos (no raw DB in UI)

Usage:
  python login_main_menu.py --db dods_cars.sqlite3
"""
from __future__ import annotations
from sql_repo import logout_user
import sys, os, ctypes
import sql_repo
import user_repo
import admin_repo
import customer_repo

args = sql_repo.get_args(description="Dod's Cars")
sql_repo.autoinit(args.db, schema_path="schema.sql", seed_admin=True)
sql_repo.require_tables_configured(["users","cars","bookings","booking_charges","maintenance"])

BANNER = r"""
======================================
        Dod's Cars — Car Rental
======================================
"""

def error_exit(msg: str, code: int = 1) -> None:
    print(f"\nERROR: {msg}\n")
    sys.exit(code)

# ────────────────────────────────────────────────────────────────────────────────
# Menus
# ────────────────────────────────────────────────────────────────────────────────
def menu_print(role: str) -> None:
    print("\n==================== Main Menu ====================")
    if role == "admin":
        print(" 1) Cars")
        print(" 2) Bookings")
        print(" 3) Car Maintenance")
        print(" 4) Analytics Dashboard")
        print(" 5) Manage Users")
        print(" 6) Account — profile (edit my details)")
        print(" 9) Logout")
        print(" 0) Exit")
    else:
        print(" 1) View Available Cars")
        print(" 2) Book a Car")
        print(" 3) My bookings")
        print(" 4) My Account")
        print(" 9) Logout")
        print(" 0) Exit")
    print("===================================================\n")

def menu_handle(user, choice: str) -> str:
    role = user.role
    if role == "admin":
        mapping = {
            "1": "admin_cars",
            "2": "admin_bookings",
            "3": "admin_maintenance",
            "4": "admin_analytics",
            "5": "admin_users",
            "6": "account_profile",
            "9": "logout",
            "0": "exit",
        }
    else:
        mapping = {
            "1": "cust_view_available",
            "2": "cust_create_booking",
            "3": "cust_my_bookings",
            "4": "account_profile",
            "9": "logout",
            "0": "exit",
        }

    act = mapping.get(choice)
    if act is None:
        print("Please choose a valid option.")
        return "continue"
    if act == "logout":
        return "logout"
    if act == "exit":
        return "exit"

    # Customer
    if act == "cust_view_available":
        customer_repo.cust_view_available()
        return "continue"
    if act == "cust_create_booking":
        customer_repo.cust_create_booking(user)
        return "continue"
    if act == "cust_my_bookings":
        customer_repo.cust_my_bookings(user)
        return "continue"

    # Admin (delegated)
    if act == "admin_cars":
        admin_repo.admin_cars_menu()
        return "continue"
    if act == "admin_bookings":
        admin_repo.admin_bookings_menu()   # includes list/approve/reject and create-on-behalf
        return "continue"
    if act == "admin_maintenance":
        admin_repo.admin_maintenance_menu()
        return "continue"
    if act == "admin_users":
        user_repo.users_admin_menu()       # or admin_repo.admin_users_menu() if you wrapped it there
        return "continue"
    if act == "account_profile":
        user_repo.profile_menu(user)
        return "continue"
    if act == "admin_analytics":
        admin_repo.admin_analytics_menu()
        return "continue"
    print(f"> {act}")
    return "continue"

# ────────────────────────────────────────────────────────────────────────────────
# For Portability - One Click Run
# ────────────────────────────────────────────────────────────────────────────────
def _resource_path(name: str) -> str:
    # Works both in source and PyInstaller
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)

def _data_dir(per_user: bool = True) -> str:
    """
    Per-user app data (default): %LOCALAPPDATA%\DodCars
    Machine-wide (shared):      %ProgramData%\DodCars
    """
    if os.name == "nt":
        root = os.environ.get("LOCALAPPDATA" if per_user else "ProgramData", os.path.expanduser("~"))
        p = os.path.join(root, "DodCars")
    else:
        p = os.path.join(os.path.expanduser("~"), ".local", "share", "DodCars")
    os.makedirs(p, exist_ok=True)
    return p

# ---- Windows Hidden attribute helpers ----
_FILE_ATTRIBUTE_HIDDEN = 0x2

def _hide_windows(path: str) -> None:
    if os.name != "nt" or not os.path.exists(path):
        return
    try:
        k32 = ctypes.windll.kernel32
        attrs = k32.GetFileAttributesW(path)
        if attrs != 0xFFFFFFFF:
            k32.SetFileAttributesW(path, attrs | _FILE_ATTRIBUTE_HIDDEN)
    except Exception:
        pass
# ────────────────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────────────────
def main() -> int:
    print(BANNER)

   # Try to get args from sql_repo, but fall back to sane defaults for EXE double-click
    per_user = True            # <-- set to False if you prefer %ProgramData%\DodCars (shared DB)
    explicit_db = any(a.startswith("--db") for a in sys.argv)

    try:
        args = sql_repo.get_args(description="Dod's Cars")
        schema_path = getattr(args, "schema", None) or _resource_path("schema.sql")
        if explicit_db:
            db_path = args.db
        else:
            db_path = os.path.join(_data_dir(per_user=per_user), "dods_cars.sqlite3")
    except Exception:
        schema_path = _resource_path("schema.sql")
        db_path = os.path.join(_data_dir(per_user=per_user), "dods_cars.sqlite3")

    # Ensure runtime files live there too (optional: set working dir)
    os.chdir(os.path.dirname(db_path))

    # First-run init (admin-only seed, per your updated sql_repo)
    sql_repo.autoinit(db_path, schema_path=schema_path, seed_admin=True)

    # Enforce non-empty values on INSERTs (repo-level guard)
    try:
        sql_repo.set_insert_require_nonempty(True)
    except Exception:
        pass

    # Ensure required tables are present
    sql_repo.require_tables_configured(
        ["users", "cars", "bookings", "booking_charges", "maintenance"]
    )
    # Quick extra check for user table
    user_repo.ensure_schema()

    while True:
        # Offer login or sign up; returns a User object
        user = user_repo.login_or_signup()
        if not user:
            print("Goodbye.\n")
            return 1

        # Session loop
        while True:
            menu_print(user.role)
            try:
                choice = input("Choose: ").strip()
            except (EOFError, KeyboardInterrupt):
                logout_user()
                print("\nGoodbye!\n")
                return 0

            state = menu_handle(user, choice)
            if state == "logout":
                logout_user()
                print("\nLogged out.\n")
                break
            if state == "exit":
                logout_user()
                print("\nGoodbye!\n")
                return 0

if __name__ == "__main__":
    sys.exit(main())
