#!/usr/bin/env python3
"""
Dod's Cars — CSV + Synthetic Seeder (3-year history)

What it does
- Seeds users, cars, and CSV-specified bookings (idempotent).
- Generates synthetic maintenance windows and additional bookings spanning the last 3 years:
  * Maintenance: 1–3 windows per car per year, 2–5 days each.
  * Bookings: realistic lengths within car min/max; ~70% approved (conflict-free), ~30% pending (may overlap).
- All DB writes go through sql_repo (no raw sqlite3).
- Safe to re-run: checks for existing rows first.

Default DB path (when no --db):
  %LOCALAPPDATA%\\DodCars\\dods_cars.sqlite3  (Windows)
  ~/.local/share/DodCars/dods_cars.sqlite3     (macOS/Linux)
"""
from __future__ import annotations
import os, sys, csv, re, random
from pathlib import Path
from datetime import date, timedelta, datetime

import sql_repo
from user_repo import UserRepo, DomainError as UserDomainError, RepoError as UserRepoError

# ---------- resource helpers (work with PyInstaller) ----------
def _resource_path(name: str) -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base = Path(__file__).resolve().parent
    return (base / name)

def _default_data_dir() -> Path:
    if os.name == "nt":
        root = os.environ.get("LOCALAPPDATA", str(Path.home()))
        p = Path(root) / "DodCars"
    else:
        p = Path.home() / ".local" / "share" / "DodCars"
    p.mkdir(parents=True, exist_ok=True)
    return p

def _default_db_path() -> Path:
    return _default_data_dir() / "dods_cars.sqlite3"

# ---------- defaults (created only if CSVs are missing) ----------
DEFAULT_USERS = """full_name,role,email,password
Albus Dumbledore,admin,,ElderWand123!
Minerva McGonagall,admin,,ElderWand123!
Severus Snape,admin,,ElderWand123!
Harry Potter,customer,,Magic123!
Hermione Granger,customer,,Magic123!
Ron Weasley,customer,,Magic123!
Ginny Weasley,customer,,Magic123!
Luna Lovegood,customer,,Magic123!
Neville Longbottom,customer,,Magic123!
Cho Chang,customer,,Magic123!
Cedric Diggory,customer,,Magic123!
Draco Malfoy,customer,,Magic123!
Pansy Parkinson,customer,,Magic123!
Dean Thomas,customer,,Magic123!
Seamus Finnigan,customer,,Magic123!
Lavender Brown,customer,,Magic123!
Parvati Patil,customer,,Magic123!
Padma Patil,customer,,Magic123!
"""

DEFAULT_CARS = """year,make,model,color,mileage,daily_rate,min_rent_days,max_rent_days,available_now
2021,Toyota,Corolla,Silver,32000,59,1,30,1
2020,Toyota,Camry,Blue,48000,69,1,30,1
2022,Honda,Civic,White,21000,62,1,30,1
2021,Mazda,3,Red,27000,60,1,30,1
2019,Ford,Focus,Grey,54000,55,1,30,1
2021,Nissan,Leaf,Green,23000,64,1,30,1
2023,Tesla,Model 3,White,12000,95,1,30,1
2020,Hyundai,i30,Black,36000,58,1,30,1
2019,Kia,Sportage,Blue,61000,72,1,30,1
2022,Subaru,Outback,Brown,19000,80,1,30,1
"""

# bookings: user_email (or full_name), car_key("year make model"), start_date, end_date, status[pending|approved]
DEFAULT_BOOKINGS = """user_email,car_key,start_date,end_date,status
hpotter@hogwarts.test,2021 Toyota Corolla,2025-09-20,2025-09-23,approved
hgranger@hogwarts.test,2023 Tesla Model 3,2025-09-22,2025-09-25,pending
rweasley@hogwarts.test,2022 Honda Civic,2025-09-24,2025-09-27,approved
llovegood@hogwarts.test,2021 Mazda 3,2025-09-28,2025-10-01,pending
mmcgonagall@hogwarts.test,2020 Toyota Camry,2025-09-21,2025-09-23,approved
ssnape@hogwarts.test,2022 Subaru Outback,2025-09-26,2025-09-29,approved
"""

# ---------- CSV utils ----------
def _ensure_csv(path: Path, content: str) -> Path:
    if not path.exists():
        path.write_text(content.strip() + "\n", encoding="utf-8")
    return path

def _open_csv_any(base_dir: Path, filename: str, default: str) -> Path:
    rp = _resource_path(filename)
    if rp.exists():
        return rp
    fp = base_dir / filename
    if fp.exists():
        return fp
    return _ensure_csv(fp, default)

def _short_email(full_name: str, taken: set[str]) -> str:
    # e.g., "Harry Potter" -> "hpotter@hogwarts.test"
    name = re.sub(r"[^A-Za-z\s'-]", "", full_name).strip()
    parts = [p for p in re.split(r"[\s'-]+", name) if p]
    base = "user" if not parts else (parts[0][0] + parts[-1]).lower()
    email = f"{base}@hogwarts.test"
    i = 2
    while email in taken:
        email = f"{base}{i}@hogwarts.test"
        i += 1
    taken.add(email)
    return email

# ---------- helpers: date + overlap ----------
def _parse(d: str) -> date:
    return datetime.strptime(d, "%Y-%m-%d").date()

def _fmt(d: date) -> str:
    return d.isoformat()

def _days(s: date, e: date) -> int:
    n = (e - s).days
    if n <= 0:
        raise ValueError("end_date must be after start_date")
    return n

def _ranges_overlap(a1: date, a2: date, b1: date, b2: date) -> bool:
    # Overlap if: a1 < b2 and a2 > b1 (half-open logic)
    return a1 < b2 and a2 > b1

# ---------- Seeders ----------
def seed_users(csv_path: Path) -> None:
    print(f"Seeding users from {csv_path.name} …")
    urepo = UserRepo()

    # existing emails for generation
    taken = {u.email for u in urepo.list_all()}

    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            full_name = (row.get("full_name") or "").strip()
            role = (row.get("role") or "customer").strip().lower()
            email = (row.get("email") or "").strip().lower()
            pwd = (row.get("password") or "").strip()
            if not full_name:
                continue
            if not email:
                email = _short_email(full_name, taken)
            if urepo.get_by_email(email):
                print(f"  = exists: {email}")
                continue
            if not pwd:
                pwd = "Welcome123!"
            with sql_repo.repo().conn:
                created = urepo.auth_signup(email=email, full_name=full_name, password=pwd, role=role)
            print(f"  + user: {created.full_name} <{created.email}> ({created.role})")

def seed_cars(csv_path: Path) -> None:
    print(f"Seeding cars from {csv_path.name} …")
    r = sql_repo.repo()
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                year = int(row["year"])
                make = row["make"].strip()
                model = row["model"].strip()
                color = (row.get("color") or "Unknown").strip()
                mileage = int(row.get("mileage") or 0)
                rate = float(row.get("daily_rate") or 0)
                min_days = int(row.get("min_rent_days") or 1)
                max_days = int(row.get("max_rent_days") or 30)
                available_now = int(row.get("available_now") or 1)
            except Exception:
                continue

            # idempotent uniqueness heuristic
            existing = r.select("cars", where={"make__eq": make, "model__eq": model, "year__eq": year, "color__eq": color}, columns=["car_id"])
            if existing:
                print(f"  = exists: {year} {make} {model} ({color})")
                continue

            with r.conn:
                cid = r.insert("cars", {
                    "year": year, "make": make, "model": model, "color": color,
                    "mileage": mileage, "daily_rate": rate,
                    "min_rent_days": min_days, "max_rent_days": max_days,
                    "available_now": available_now
                })
            print(f"  + car: #{cid} {year} {make} {model} ({color}) ${rate}/day")

def seed_bookings_from_csv(csv_path: Path) -> None:
    print(f"Seeding CSV bookings from {csv_path.name} …")
    urepo = UserRepo()
    r = sql_repo.repo()

    def resolve_car_id(car_key: str) -> int | None:
        m = re.match(r"^\s*(\d{4})\s+([A-Za-z0-9]+)\s+(.+?)\s*$", car_key)
        if not m:
            return None
        year = int(m.group(1)); make = m.group(2).strip(); model = m.group(3).strip()
        cars = r.select("cars", where={"year__eq": year, "make__eq": make, "model__eq": model}, columns=["car_id"])
        return cars[0]["car_id"] if cars else None

    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            user_email = (row.get("user_email") or "").strip().lower()
            user_full = (row.get("user_full") or "").strip()
            car_key   = (row.get("car_key") or "").strip()
            car_id    = row.get("car_id")
            start     = (row.get("start_date") or "").strip()
            end       = (row.get("end_date") or "").strip()
            status    = (row.get("status") or "pending").strip().lower()

            # resolve user
            user = None
            if user_email:
                user = urepo.get_by_email(user_email)
            if not user and user_full:
                guess = _short_email(user_full, set())
                user = urepo.get_by_email(guess)
            if not user:
                print(f"  ! skip: no user for row ({user_email or user_full})")
                continue

            # resolve car
            cid = None
            if car_id and str(car_id).strip().isdigit():
                cid = int(car_id)
            elif car_key:
                cid = resolve_car_id(car_key)
            if not cid:
                print(f"  ! skip: no car for row ({car_key or car_id})")
                continue

            # idempotency: same (user, car, start)
            exist = r.select_one("bookings", where={"user_id__eq": user.id, "car_id__eq": cid, "start_date__eq": start}, columns=["booking_id"])
            if exist:
                print(f"  = exists: booking for {user.email} car#{cid} {start}")
                continue

            # compute days + total (from car rate)
            car = r.select_one("cars", where={"car_id__eq": cid})
            s, e = _parse(start), _parse(end)
            days = _days(s, e)
            total = float(car["daily_rate"]) * days

            with r.conn:
                bid = r.insert("bookings", {
                    "user_id": user.id, "car_id": cid,
                    "start_date": _fmt(s), "end_date": _fmt(e),
                    "rental_days": days, "total_fee": total,
                    "status": "approved" if status == "approved" else "pending",
                })
            print(f"  + booking: #{bid} {user.email} -> car#{cid} {start}→{end} [{status}]")

# ---------- Synthetic generation over last 3 years ----------
def _load_all_users_and_cars():
    r = sql_repo.repo()
    users = r.select("users", columns=["user_id","email","role"])
    users = [u for u in users if (u["role"] == "customer")]
    cars  = r.select("cars", columns=["car_id","daily_rate","min_rent_days","max_rent_days","year","make","model"])
    return users, cars

def _maintenance_exists(car_id: int, start: date) -> bool:
    r = sql_repo.repo()
    return r.select_one("maintenance", where={"car_id__eq": car_id, "start_date__eq": _fmt(start)}) is not None

def _insert_maintenance(car_id: int, type_: str, cost: float, s: date, e: date | None, note: str) -> int:
    r = sql_repo.repo()
    with r.conn:
        return r.insert("maintenance", {
            "car_id": car_id, "type": type_, "cost": cost,
            "start_date": _fmt(s), "end_date": (_fmt(e) if e else None),
            "notes": note
        })

def _booking_exists(user_id: int, car_id: int, s: date) -> bool:
    r = sql_repo.repo()
    return r.select_one("bookings", where={"user_id__eq": user_id, "car_id__eq": car_id, "start_date__eq": _fmt(s)}) is not None

def _approved_windows_for_car(car_id: int):
    r = sql_repo.repo()
    rows = r.select("bookings", where={"car_id__eq": car_id, "status__eq": "approved"}, columns=["start_date","end_date"])
    return [(_parse(x["start_date"]), _parse(x["end_date"])) for x in rows]

def _maintenance_windows_for_car(car_id: int):
    r = sql_repo.repo()
    rows = r.select("maintenance", where={"car_id__eq": car_id}, columns=["start_date","end_date"])
    out = []
    for x in rows:
        s = _parse(x["start_date"])
        e = _parse(x["end_date"]) if x.get("end_date") else s + timedelta(days=3)  # open = assume 3d window for overlap checks
        out.append((s, e))
    return out

def _conflicts(car_id: int, s: date, e: date) -> bool:
    for (as_, ae) in _approved_windows_for_car(car_id):
        if _ranges_overlap(as_, ae, s, e):
            return True
    for (ms, me) in _maintenance_windows_for_car(car_id):
        if _ranges_overlap(ms, me, s, e):
            return True
    return False

def generate_maintenance_and_bookings(years: int = 3, seed: int = 42) -> None:
    """
    Generate maintenance + bookings across the last `years` years.
    - Maintenance: 1–3 periods per car per year, 2–5 days, cost 120–900.
    - Bookings: for each car/month, 0–2 bookings; ~70% approved (conflict-free), ~30% pending (may overlap).
    """
    random.seed(seed)
    r = sql_repo.repo()
    users, cars = _load_all_users_and_cars()
    if not users or not cars:
        print("  ! Skipping synthetic data: need at least 1 customer and 1 car.")
        return

    today = date.today()
    start_horizon = today - timedelta(days=365*years)
    types = ["service", "repair", "WOF"]

    # --- Maintenance ---
    print("Generating synthetic maintenance …")
    for c in cars:
        cid = int(c["car_id"])
        # deterministic per-car seed (stable across runs)
        rnd = random.Random(seed + cid)
        for y in range(years):
            year_start = date(today.year - y, 1, 1)
            year_end = date(today.year - y, 12, 31)
            # clip to horizon
            s0 = max(year_start, start_horizon)
            e0 = min(year_end, today)
            periods = rnd.randint(1, 3)
            for _ in range(periods):
                # pick a random start inside the window
                span = (e0 - s0).days - 6  # leave space for up to 5 days
                if span <= 0:
                    continue
                start_off = rnd.randint(0, max(0, span))
                s = s0 + timedelta(days=start_off)
                length = rnd.randint(2, 5)
                e = s + timedelta(days=length)
                # idempotent guard
                if _maintenance_exists(cid, s):
                    continue
                cost = float(rnd.randint(120, 900))
                note = "SEED: auto"
                _insert_maintenance(cid, rnd.choice(types), cost, s, e, note)
                # cache is DB-backed; fine to re-query later

    # --- Bookings ---
    print("Generating synthetic bookings …")
    for c in cars:
        cid = int(c["car_id"])
        min_d = int(c["min_rent_days"])
        max_d = int(c["max_rent_days"])
        # per-car RNG to keep stability
        rnd = random.Random(seed * 997 + cid)

        # month by month over horizon: 0–2 bookings per month
        cur = date(start_horizon.year, start_horizon.month, 1)
        while cur <= today:
            # pick how many bookings this month
            count = rnd.randint(0, 2)
            for _ in range(count):
                # choose user
                u = rnd.choice(users)
                uid = int(u["user_id"])
                # choose start day in this month (keep within month bounds)
                month_end = (date(cur.year + (cur.month // 12), (cur.month % 12) + 1, 1) - timedelta(days=1))
                span = (month_end - cur).days - (max_d + 1)
                if span <= 0:
                    continue
                start_day_off = rnd.randint(0, max(0, span))
                s = cur + timedelta(days=start_day_off)
                # length within car rules
                days = rnd.randint(min_d, max(min(max_d, min_d + 6), min_d))  # keep most rentals short-ish
                e = s + timedelta(days=days)
                # Decide approved vs pending
                is_approved = rnd.random() < 0.70
                if is_approved and _conflicts(cid, s, e):
                    # cannot approve a conflicting booking; downgrade to pending
                    is_approved = False

                # idempotent guard
                if _booking_exists(uid, cid, s):
                    continue

                # compute fee
                rate = float(c["daily_rate"])
                total = rate * days
                with r.conn:
                    r.insert("bookings", {
                        "user_id": uid, "car_id": cid,
                        "start_date": _fmt(s), "end_date": _fmt(e),
                        "rental_days": days, "total_fee": total,
                        "status": ("approved" if is_approved else "pending"),
                    })
            # next month
            next_month = (cur.month % 12) + 1
            next_year = cur.year + (1 if cur.month == 12 else 0)
            cur = date(next_year, next_month, 1)

# ---------- main ----------
def main():
    # DB/schema setup (auto — no args required)
    try:
        args = sql_repo.get_args(description="Dod's Cars — CSV + Synthetic Seeder")
        db_path = Path(args.db) if getattr(args, "db", None) else _default_db_path()
        schema_path = Path(getattr(args, "schema", "schema.sql"))
    except Exception:
        db_path = _default_db_path()
        schema_path = _resource_path("schema.sql")

    # configure + create schema (admin-only seed handled by app normally; ok if already exists)
    try:
        sql_repo.autoinit(str(db_path), schema_path=str(schema_path), seed_admin=True)
        sql_repo.require_tables_configured(["users","cars","bookings","booking_charges","maintenance"])
    except Exception as e:
        print(f"(autoinit) {e}")

    # find CSVs: prefer packaged; else create defaults in data dir
    data_dir = _default_data_dir()
    users_csv    = _open_csv_any(data_dir, "users.csv",    DEFAULT_USERS)
    cars_csv     = _open_csv_any(data_dir, "cars.csv",     DEFAULT_CARS)
    bookings_csv = _open_csv_any(data_dir, "bookings.csv", DEFAULT_BOOKINGS)

    # seed base CSVs
    try:
        seed_users(users_csv)
        seed_cars(cars_csv)
        seed_bookings_from_csv(bookings_csv)
    except (UserRepoError, UserDomainError) as ex:
        print(f"\n❌ Error seeding CSVs: {ex}")

    # generate last 3 years synthetic maintenance + bookings
    try:
        generate_maintenance_and_bookings(years=3, seed=42)
        print("\n✅ Seeding complete (CSV + 3-year synthetic).")
    except Exception as ex:
        print(f"\n❌ Error generating synthetic data: {ex}")

if __name__ == "__main__":
    main()
