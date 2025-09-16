#!/usr/bin/env python3
"""
Assessment 1 - Car System - Dod's Cars
PSEASS - EJI
Eduardo JR Ilagan

user_repo.py — Users Repository + Interactive helper (compat with old menu)

Purpose
- Encapsulate User data access and authentication rules (Repository).
- Provide a small interactive helper `login_or_signup()` for legacy menus.

Design
- Pattern: Repository + (injected) Factory (ABC) for row→object mapping
- Passwords: PBKDF2-HMAC(SHA-256), random 16-byte salt, 200k iterations
- Transactions: callers may group multi-step ops with sql_repo.transaction()

Use-Case Mapping (logical support)
- UC-Auth: Login / Signup
  • auth_login(email, password), auth_signup(email, full_name, password, role="customer")
- UC-Account: Profile / Password Maintenance
  • get_by_id(...), update_profile(...), change_password(...)
- Admin: Manage Users (list/create/update/delete)
  • list_all(), create(...), save(...), delete(...)

Notes
- Mapping uses an injected UserFactoryABC; a default factory is provided.
- `login_or_signup()` keeps the UI DB-free by reusing sql_repo prompt validators.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

import sys, binascii, hashlib, secrets, getpass
from base_repo import UserFactoryABC
from sql_repo import (
    repo as _repo,
    SqlError,
    require_tables_configured,
    prompt_required_text,
    session as _session,
    login_user,
)

# ────────────────────────────────────────────────────────────────────────────────
# Errors
# ────────────────────────────────────────────────────────────────────────────────
class RepoError(Exception): ...
class DomainError(Exception): ...

# ────────────────────────────────────────────────────────────────────────────────
# Domain model
# ────────────────────────────────────────────────────────────────────────────────
@dataclass
class User:
    # if you have __init__, ensure it assigns to public attrs:
    def __init__(self, id, email, full_name, role,
                 created_at=None, pass_hash=None, salt=None, active=None):
        self.id = id
        self.email = email
        self.full_name = full_name
        self.role = role
        self.created_at = created_at
        self.pass_hash = pass_hash   # <-- public
        self.salt = salt             # <-- public
        self.active = active         # if you support 'active'

    # Password methods (encapsulated, but use public attrs)
    def set_password(self, plain: str) -> None:
        ph, s = _hash_password(plain)
        self.pass_hash = ph
        self.salt = s

    def verify_password(self, plain: str) -> bool:
        ph = getattr(self, "pass_hash", None)
        s = getattr(self, "salt", None)
        if not ph or not s:
            return False
        return verify_password(plain, ph, s)
# ────────────────────────────────────────────────────────────────────────────────
# Default Factory (row → domain)
# ────────────────────────────────────────────────────────────────────────────────
class _DefaultUserFactory(UserFactoryABC):
    def user_from_row(self, row: dict | None):
        if not row:
            return None
        # DB uses 'user_id'; entity ctor expects 'id'
        uid = row.get("user_id")
        if uid is None:
            uid = row.get("id")  # tolerate schemas that use 'id'

        return User(
            id=uid,
            email=row.get("email", "") or "",
            full_name=row.get("full_name", "") or "",
            role=(row.get("role") or "customer").strip().lower(),
            created_at=row.get("created_at"),
            pass_hash=_coerce_hex(row.get("pass_hash")),
            salt=_coerce_hex(row.get("salt")),
            # If your User class includes 'active', you can pass it too:
            active=row.get("active")
        )
# ────────────────────────────────────────────────────────────────────────────────
# Password hashing 
# ────────────────────────────────────────────────────────────────────────────────
PBKDF_ROUNDS = 200_000

def _hash_password(password: str) -> tuple[str, str]:
    """
    Returns (pass_hash_hex, salt_hex) using PBKDF2-HMAC(SHA-256).
    Hash and salt are lowercase hex strings (same as the old build).
    """
    if not password or len(password) < 8:
        raise DomainError("Password must be at least 8 characters.")
    import secrets, hashlib, binascii
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF_ROUNDS)
    return binascii.hexlify(dk).decode("ascii").lower(), binascii.hexlify(salt).decode("ascii").lower()


def verify_password(plain: str, pass_hash_hex: str, salt_hex: str) -> bool:
    """
    Verifies plain text password against the stored hex hash/salt.
    """
    import hashlib, binascii
    try:
        salt = binascii.unhexlify((salt_hex or "").strip())
        want = (pass_hash_hex or "").strip().lower()
    except Exception:
        return False
    got = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, PBKDF_ROUNDS)
    return binascii.hexlify(got).decode("ascii").lower() == want

# (Optional) tolerate older rows stored as BLOBs/memoryview
def _coerce_hex(x):
    if x is None: return None
    if isinstance(x, memoryview): x = x.tobytes()
    if isinstance(x, bytes):
        try: return x.hex()
        except Exception: return x.decode("ascii", "ignore").lower()
    return str(x).strip().lower()

# ────────────────────────────────────────────────────────────────────────────────
# Schema guard (optional helper for callers)
# ────────────────────────────────────────────────────────────────────────────────
def ensure_schema() -> None:
    try:
        require_tables_configured(["users"])
    except SqlError as e:
        raise RuntimeError(str(e))

# ==============================================================================
# UserRepo — Repository (uses UserFactoryABC for mapping)
# ==============================================================================
class UserRepo:
    """
    Users repository.
    - UC-Auth: auth_login, auth_signup
    - UC-Account: get/update profile, change password
    - Admin: list/create/update/delete users
    """

    def __init__(self, factory: UserFactoryABC | None = None):
        self.sql = _repo()
        self._f: UserFactoryABC = factory or _DefaultUserFactory()

    # ──────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────
    def _users_has_active(self) -> bool:
        try:
            return "active" in (self.sql._schema.get("users") or set())
        except Exception:
            return False

    def ensure_unique_email(self, email: str, ignore_user_id: Optional[int] = None) -> None:
        row = self.sql.select_one("users", where={"email__eq": email}, columns=["user_id"])
        if row and (ignore_user_id is None or int(row["user_id"]) != int(ignore_user_id)):
            raise RepoError("Email already in use.")

    # ──────────────────────────────────────────────────────────────────────
    # Reads
    # ──────────────────────────────────────────────────────────────────────
    def get_by_id(self, user_id: int):
        row = self.sql.select_one("users", where={"user_id__eq": user_id})
        return self._f.user_from_row(row)

    def get_by_email(self, email: str):
        e = email.strip().lower()
        row = self.sql.select_one("users", where={"email__eq": e})
        return self._f.user_from_row(row)

    def list_all(self, role: str | None = None, search: str | None = None):
        where = {}
        if role:
            r = role.strip().lower()
            if r not in ("customer", "admin"):
                raise RepoError("Role filter must be 'customer' or 'admin'.")
            where["role__eq"] = r

        if search:
            s = f"%{search.strip()}%"
            seen: dict[int, dict] = {}
            for r in self.sql.select("users", where={"email__like": s}, order=[("created_at", "DESC")]):
                seen[r["user_id"]] = r
            for r in self.sql.select("users", where={"full_name__like": s}, order=[("created_at", "DESC")]):
                seen[r["user_id"]] = r
            return [self._f.user_from_row(r) for r in seen.values()]

        rows = self.sql.select("users", where=where, order=[("created_at", "DESC")])
        return [self._f.user_from_row(r) for r in rows]

    # ──────────────────────────────────────────────────────────────────────
    # Writes (Admin)
    # ──────────────────────────────────────────────────────────────────────
    def create(self, user: User, *, password: Optional[str] = None) -> User:
        self.ensure_unique_email(user.email)

        # Ensure credentials are present on the entity
        if password is not None:
            user.set_password(password)
        if not getattr(user, "pass_hash", None) or not getattr(user, "salt", None):
            raise DomainError("Password is required. Set with user.set_password(...) or pass password=...")

        values = {
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "pass_hash": user.pass_hash,   # <-- public, not _pass_hash
            "salt": user.salt,             # <-- public, not _salt
        }
        if self._users_has_active():
            values["active"] = 1

        # Commit this single-step write
        with self.sql.conn:
            uid = self.sql.insert("users", values)

        created = self.get_by_id(uid)
        if not created:
            raise RepoError("Failed to create user.")
        return created

    def save(self, user: User) -> int:
        if not getattr(user, "id", None):
            raise RepoError("User id required for update.")
        changes = {
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
        }
        if self._users_has_active() and hasattr(user, "active"):
            changes["active"] = 1 if (getattr(user, "active") is None) else int(getattr(user, "active"))
        with self.sql.conn:
            return self.sql.update("users", where={"user_id__eq": int(user.id)}, changes=changes)


    def delete(self, user_id: int) -> int:
        with self.sql.conn:
            return self.sql.delete("users", where={"user_id__eq": int(user_id)})

    # ──────────────────────────────────────────────────────────────────────
    # Authentication (UC-Auth)
    # ──────────────────────────────────────────────────────────────────────
    def auth_signup(self, email: str, full_name: str, password: str, *, role: str = "customer") -> User:
        u = User(None, email=email, full_name=full_name, role=role.strip().lower())
        # create() will set_password(...) and commit
        return self.create(u, password=password)

    def auth_login(self, email: str, password: str) -> User:
        u = self.get_by_email(email)
        if not u or not u.verify_password(password):
            raise DomainError("Invalid email or password.")
        if self._users_has_active() and getattr(u, "active", 1) in (0, "0"):
            raise DomainError("Account is inactive.")
        return u


    # ──────────────────────────────────────────────────────────────────────
    # Account Maintenance (UC-Account)
    # ──────────────────────────────────────────────────────────────────────
    def change_password(self, user_id: int, new_password: str) -> int:
        u = self.get_by_id(user_id)
        if not u:
            raise RepoError("User not found.")
        ph, salt = _hash_password(new_password)  # (hash_hex, salt_hex)
        with self.sql.conn:
            return self.sql.update(
                "users",
                where={"user_id__eq": int(user_id)},
                changes={"pass_hash": ph, "salt": salt},
            )

    def update_profile(self, user_id: int, *, full_name: Optional[str] = None, email: Optional[str] = None) -> int:
        if full_name is None and email is None:
            return 0
        changes: Dict[str, Any] = {}
        if full_name is not None:
            changes["full_name"] = full_name.strip()
        if email is not None:
            if "@" not in email:
                raise DomainError("A valid email is required.")
            self.ensure_unique_email(email.strip().lower(), ignore_user_id=int(user_id))
            changes["email"] = email.strip().lower()
        with self.sql.conn:
            return self.sql.update("users", where={"user_id__eq": int(user_id)}, changes=changes)

def prompt_password_twice(msg1: str = "Password: ", msg2: str = "Re-type password: ") -> str:
    """Prompt for a password twice (masked) and ensure they match."""
    while True:
        p1 = prompt_password(msg1)
        p2 = prompt_password(msg2)
        if p1 == p2:
            return p1
        print("Passwords do not match. Please try again.")

def prompt_password(prompt: str = "Password: ") -> str:
    """
    Prompt for a password, masking input with * for each character.
    Works on Windows and Unix.
    """
    try:
        import termios, tty
    except ImportError:
        # Windows fallback: use msvcrt
        import msvcrt
        print(prompt, end="", flush=True)
        buf = []
        while True:
            ch = msvcrt.getch()
            if ch in {b"\r", b"\n"}:  # Enter
                print("")
                break
            elif ch == b"\x08":  # Backspace
                if buf:
                    buf.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
            elif ch == b"\x03":  # Ctrl-C
                raise KeyboardInterrupt
            else:
                buf.append(ch.decode("utf-8"))
                sys.stdout.write("*")
                sys.stdout.flush()
        return "".join(buf)
    else:
        # Unix implementation
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            print(prompt, end="", flush=True)
            buf = []
            while True:
                ch = sys.stdin.read(1)
                if ch in {"\r", "\n"}:
                    print("")
                    break
                elif ch == "\x7f":  # Backspace
                    if buf:
                        buf.pop()
                        sys.stdout.write("\b \b")
                        sys.stdout.flush()
                elif ch == "\x03":  # Ctrl-C
                    raise KeyboardInterrupt
                else:
                    buf.append(ch)
                    sys.stdout.write("*")
                    sys.stdout.flush()
            return "".join(buf)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

# ────────────────────────────────────────────────────────────────────────────────
# Interactive login/register helper for legacy menus (keeps UI DB-free)
# ────────────────────────────────────────────────────────────────────────────────
def login_or_signup():
    """
    Console helper used by login_main_menu.py.
    Returns a User on success, or None if the user chose to exit.
    """
    ensure_schema()
    repo = UserRepo()

    while True:
        print("\n1) Sign In")
        print("2) Sign Up")
        print("0) Exit")
        choice = input("Choice: ").strip()

        if choice == "1":
            print("\n=== Sign In ===")
            email = prompt_required_text("Email ")
            password = prompt_password("Password: ")
            try:
                user = repo.auth_login(email, password)
                login_user(user)
                print(f"Signed in as {user.full_name}.\n")
                return user
            except DomainError as e:
                print(f"{e}")

        elif choice == "2":
            print("\n=== Sign Up ===")
            full_name = prompt_required_text("Full name: ")
            email = prompt_required_text("Email: ")
            password = prompt_password_twice("Password: ", "Re-type password: ")
            try:
                user = repo.auth_signup(email=email, full_name=full_name, password=password, role="customer")
                login_user(user)
                print(f"Account created. Signed in as {user.full_name}.\n")
                return user
            except DomainError as e:
                print(f"{e}")

        elif choice == "0":
            return None

        else:
            print("Please choose a valid option.")

# ────────────────────────────────────────────────────────────────────────────────
# Interactive Profile Menu 
# ────────────────────────────────────────────────────────────────────────────────
def profile_menu(user: "User"):
    """
    Simple CLI for viewing/updating profile and changing password.
    Returns the (possibly updated) User; 'Back' keeps the current user.
    """
    ensure_schema()
    repo = UserRepo()

    def _refresh() -> "User":
        u = repo.get_by_id(int(user.id))
        return u or user

    while True:
        user = _refresh()
        print(f"\n=== Profile — {user.full_name} ({user.email}) ===")
        print("1) View profile")
        print("2) Change full name")
        print("3) Change email")
        print("4) Change password")
        print("0) Back")
        choice = input("Choice: ").strip()

        if choice == "1":
            print(f"\nName : {user.full_name}")
            print(f"Email: {user.email}")
            print(f"Role : {user.role}")
            print(f"Active: {('Yes' if (user.active or 1) else 'No')}")
        elif choice == "2":
            new_name = prompt_required_text("New full name")
            try:
                repo.update_profile(user.id, full_name=new_name)
                print("Full name updated.")
            except DomainError as e:
                print(e)
        elif choice == "3":
            new_email = prompt_required_text("New email")
            try:
                repo.update_profile(user.id, email=new_email)
                print("Email updated.")
            except DomainError as e:
                print(e)
        elif choice == "4":
            # optional current password check for safety
            try:
                curr = prompt_password("Current password: ")
                # will raise if wrong
                repo.auth_login(user.email, curr)
            except DomainError:
                print("Current password is incorrect.")
                continue
            new_pw1 = prompt_password_twice("New Password: ", "Re-type New password: ")
            try:
                repo.change_password(user.id, new_pw1)
                print("Password changed.")
            except DomainError as e:
                print(e)
        elif choice == "0":
            return user
        else:
            print("Please choose a valid option.")

# ────────────────────────────────────────────────────────────────────────────────
# Interactive Admin → Users Menu (used by login_main_menu.py)
# ────────────────────────────────────────────────────────────────────────────────
def users_admin_menu():
    """
    Admin console to manage users.
    Actions: list, create, edit (name/email/role/active), reset password, delete.
    """
    ensure_schema()
    repo = UserRepo()

    # Optional: prevent accidental self-delete if session singleton exists
    current_user_id = None
    if getattr(_session, "user", None) and getattr(_session.user, "id", None):
        current_user_id = int(_session.user.id)

    def yn(prompt: str) -> bool:
        while True:
            ans = input(f"{prompt} [y/n]: ").strip().lower()
            if ans in ("y", "yes"): return True
            if ans in ("n", "no"):  return False
            print("Please enter y or n.")

    def _pick_user(prompt: str = "User ID") -> Optional["User"]:
        try:
            uid = int(input(f"{prompt}: ").strip())
        except ValueError:
            print("Please enter a valid numeric ID.")
            return None
        u = repo.get_by_id(uid)
        if not u:
            print("User not found.")
            return None
        return u

    while True:
        print("\n=== Admin › Users ===")
        print("1) List users")
        print("2) Create user")
        print("3) Edit user (name/email/role/active)")
        print("4) Reset password")
        print("5) Delete user")
        print("0) Back")
        choice = input("Choice: ").strip()

        if choice == "1":
            users = repo.list_all()
            if not users:
                print("No users found.")
                continue
            print("\nID   Role       Active  Name                       Email")
            print("---- ---------- ------- -------------------------- ------------------------------")
            for u in users:
                active_txt = "Yes" if (u.active is None or int(u.active) != 0) else "No"
                print(f"{str(u.id).ljust(4)} {u.role.ljust(10)} {active_txt.ljust(7)} {u.full_name[:26].ljust(26)} {u.email}")

        elif choice == "2":
            print("\n=== Create user ===")
            full_name = prompt_required_text("Full name")
            email = prompt_required_text("Email")
            role = input("Role [customer/admin] (default: customer): ").strip().lower() or "customer"
            if role not in ("customer", "admin"):
                print("Role must be 'customer' or 'admin'.")
                continue
            password = prompt_password_twice("Password: ", "Re-type password: ")
            try:
                # use auth_signup to apply same validation paths
                created = repo.auth_signup(email=email, full_name=full_name, password=password, role=role)
                print(f"Created user #{created.id} ({created.full_name}, {created.role}).")
            except DomainError as e:
                print(e)

        elif choice == "3":
            print("\n=== Edit user ===")
            u = _pick_user()
            if not u:
                continue
            print(f"Editing: #{u.id} {u.full_name} <{u.email}> [{u.role}] Active={u.active}")
            print("1) Change full name")
            print("2) Change email")
            print("3) Change role (customer/admin)")
            print("4) Toggle active")
            print("0) Back")
            sub = input("Choice: ").strip().lower()
            try:
                if sub == "1":
                    new_name = prompt_required_text("New full name")
                    repo.update_profile(u.id, full_name=new_name)
                    print("Full name updated.")
                elif sub == "2":
                    new_email = prompt_required_text("New email")
                    repo.update_profile(u.id, email=new_email)
                    print("Email updated.")
                elif sub == "3":
                    new_role = input("New role [customer/admin]: ").strip().lower()
                    if new_role not in ("customer", "admin"):
                        print("Role must be 'customer' or 'admin'.")
                        continue
                    u.role = new_role
                    repo.save(u)
                    print("Role updated.")
                elif sub == "4":
                    # flip active (treat None as active=1)
                    new_active = 0 if (u.active is None or int(u.active) != 0) else 1
                    u.active = new_active
                    repo.save(u)
                    print(f"Active set to {bool(new_active)}.")
                elif sub == "x":
                    pass
                else:
                    print("Please choose a valid option.")
            except DomainError as e:
                print(e)
            except RepoError as e:
                print(e)

        elif choice == "4":
            print("\n=== Reset password ===")
            u = _pick_user()
            if not u:
                continue
            pw = prompt_password_twice("New Password: ", "Re-type password: ")
            try:
                repo.change_password(u.id, pw)
                print("Password reset.")
            except DomainError as e:
                print(e)

        elif choice == "5":
            print("\n=== Delete user ===")
            u = _pick_user()
            if not u:
                continue
            if current_user_id and int(u.id) == current_user_id:
                print("Refusing to delete the currently signed-in admin.")
                continue
            if yn(f"Delete user #{u.id} {u.full_name} <{u.email}>?"):
                try:
                    repo.delete(u.id)
                    print("User deleted.")
                except RepoError as e:
                    print(e)

        elif choice == "0":
            return
        else:
            print("Please choose a valid option.")