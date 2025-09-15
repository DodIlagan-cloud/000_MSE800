#!/usr/bin/env python3
"""
Assessment 1 - Car System - Dod's Cars
PSEASS - EJI
Eduardo JR Ilagan

user_repo.py — User operations.
- Delegates all DB work to the global repo in sql_repo.
- Includes login flow and an interactive Users Maintenance submenu.
- Domain model: User, CustomerUser, AdminUser (encapsulation + inheritance)
- Repository: UserRepo (persists via sql_repo global repo)
- Flows: login, signup, login-or-signup, self-serve profile
- Admin submenu: Users maintenance (create/list/edit/delete/reset password)

All DB work goes through: from sql_repo import repo as _repo
"""
from __future__ import annotations

import re, secrets, hashlib, binascii, getpass
from typing import Optional, List, Dict
from sql_repo import SqlRepo, SqlError, repo as _repo, require_tables_configured as _require

PBKDF_ROUNDS = 200_000
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# ────────────────────────────────────────────────────────────────────────────────
# Errors
# ────────────────────────────────────────────────────────────────────────────────
class RepoError(Exception):
    """Persistence/DB-level errors (dup email, FK constraints, etc.)."""
    pass

class DomainError(Exception):
    """Domain/business rule violations (bad email, empty name, short password)."""
    pass

def ensure_schema():
    """Fail fast if required tables/views are missing."""
    try:
        _require(["users", "cars"])
    except SqlError as e:
        raise RepoError(str(e))

# ────────────────────────────────────────────────────────────────────────────────
# Password Helpers (hash/verify)
# ────────────────────────────────────────────────────────────────────────────────
def _hash_password(password: str) -> tuple[str, str]:
    if not password or len(password) < 8:
        raise DomainError("Password must be at least 8 characters.")
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF_ROUNDS)
    return binascii.hexlify(dk).decode("ascii"), binascii.hexlify(salt).decode("ascii")

def verify_password(plain: str, pass_hash_hex: str, salt_hex: str) -> bool:
    try:
        salt = binascii.unhexlify(salt_hex)
        want = pass_hash_hex.lower()
    except Exception:
        return False
    got = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, PBKDF_ROUNDS)
    return binascii.hexlify(got).decode("ascii").lower() == want

# ────────────────────────────────────────────────────────────────────────────────
# Domain classes (encapsulation + inheritance)
# ────────────────────────────────────────────────────────────────────────────────
class User:
    """Encapsulated user: validates properties; hides pass_hash/salt behind methods."""
    def __init__(self, user_id: int | None, email: str, full_name: str, role: str,
                 created_at: str | None = None, pass_hash: str | None = None, salt: str | None = None):
        self._id = user_id
        self._email = None
        self._full_name = None
        self._role = None
        self._pass_hash = pass_hash
        self._salt = salt
        self.created_at = created_at
        self.email = email
        self.full_name = full_name
        self.role = role

    # Properties (validated access)
    @property
    def id(self) -> int | None: return self._id

    @property
    def email(self) -> str: return self._email
    @email.setter
    def email(self, value: str):
        if not value: raise DomainError("Email is required.")
        e = value.strip().lower()
        if not EMAIL_RE.match(e): raise DomainError("Invalid email format.")
        self._email = e

    @property
    def full_name(self) -> str: return self._full_name
    @full_name.setter
    def full_name(self, value: str):
        if value is None or not value.strip(): raise DomainError("Full name is required.")
        self._full_name = value.strip()

    @property
    def role(self) -> str: return self._role
    @role.setter
    def role(self, value: str):
        v = (value or "").strip().lower()
        if v not in ("customer", "admin"): raise DomainError("Role must be 'customer' or 'admin'.")
        self._role = v

    # Password methods (encapsulated)
    def set_password(self, plain: str):
        ph, salt = _hash_password(plain)
        self._pass_hash, self._salt = ph, salt

    def verify_password(self, plain: str) -> bool:
        if not self._pass_hash or not self._salt: return False
        return verify_password(plain, self._pass_hash, self._salt)

    # Safe view for UI
    def to_public(self) -> dict:
        return {"id": self.id, "email": self.email, "full_name": self.full_name, "role": self.role, "created_at": self.created_at}

class CustomerUser(User):
    def __init__(self, *args, **kwargs):
        kwargs["role"] = "customer"
        super().__init__(*args, **kwargs)

class AdminUser(User):
    def __init__(self, *args, **kwargs):
        kwargs["role"] = "admin"
        super().__init__(*args, **kwargs)

# ────────────────────────────────────────────────────────────────────────────────
# Repository (persists via sql_repo global repo)
# ────────────────────────────────────────────────────────────────────────────────
class UserRepo:
    def __init__(self):
        self.sql = _repo()

    @staticmethod
    def _row_to_user(row: Dict | None) -> User | None:
        if not row: return None
        cls = AdminUser if row.get("role") == "admin" else CustomerUser
        return cls(
            user_id=row.get("user_id"),
            email=row.get("email", ""),
            full_name=row.get("full_name", ""),
            role=row.get("role", "customer"),
            created_at=row.get("created_at"),
            pass_hash=row.get("pass_hash"),
            salt=row.get("salt"),
        )

    def get_by_id(self, user_id: int) -> User | None:
        row = self.sql.select_one("users", where={"user_id__eq": user_id})
        return self._row_to_user(row)

    def get_by_email(self, email: str) -> User | None:
        e = email.strip().lower()
        row = self.sql.select_one("users", where={"email__eq": e})
        return self._row_to_user(row)

    def list(self, role: str | None = None, search: str | None = None) -> List[User]:
        where = {}
        if role:
            r = role.strip().lower()
            if r not in ("customer", "admin"): raise RepoError("Role filter must be 'customer' or 'admin'.")
            where["role__eq"] = r
        if search:
            s = f"%{search.strip()}%"
            seen: Dict[int, Dict] = {}
            for r in self.sql.select("users", where={"email__like": s}, order=[("created_at", "DESC")]): seen[r["user_id"]] = r
            for r in self.sql.select("users", where={"full_name__like": s}, order=[("created_at", "DESC")]): seen[r["user_id"]] = r
            return [self._row_to_user(r) for r in seen.values()]
        rows = self.sql.select("users", where=where, order=[("created_at", "DESC")])
        return [self._row_to_user(r) for r in rows]

    def ensure_unique_email(self, email: str, ignore_user_id: int | None = None):
        row = self.sql.select_one("users", where={"email__eq": email}, columns=["user_id"])
        if row and (ignore_user_id is None or row["user_id"] != ignore_user_id):
            raise RepoError("Email already in use.")

    def create(self, user: User) -> User:
        self.ensure_unique_email(user.email)
        new_id = self.sql.insert("users", {
            "email": user.email,
            "pass_hash": user._pass_hash,
            "salt": user._salt,
            "full_name": user.full_name,
            "role": user.role,
        })
        user._id = new_id
        return user

    def save_profile(self, user: User) -> int:
        self.ensure_unique_email(user.email, ignore_user_id=user.id)
        return self.sql.update("users", where={"user_id__eq": user.id},
                               changes={"email": user.email, "full_name": user.full_name, "role": user.role})

    def save_password(self, user: User) -> int:
        return self.sql.update("users", where={"user_id__eq": user.id},
                               changes={"pass_hash": user._pass_hash, "salt": user._salt})

    def delete(self, user_id: int) -> int:
        return self.sql.delete("users", where={"user_id__eq": user_id})

# ────────────────────────────────────────────────────────────────────────────────
# Flows (use classes + repo)
# ────────────────────────────────────────────────────────────────────────────────
def login_flow(max_attempts: int = 3) -> User | None:
    repo = UserRepo()
    for _ in range(max_attempts):
        print("\n--- Login ---")
        email = input("Email: ").strip().lower()
        pwd = getpass.getpass("Password: ")
        user = repo.get_by_email(email)
        if user and user.verify_password(pwd):
            print(f"\nWelcome, {user.full_name} ({user.role}).\n")
            return user
        print("Invalid email or password.\n")
    return None

def signup_flow() -> User | None:
    repo = UserRepo()
    print("\n--- Sign Up ---")
    email = input("Email: ").strip().lower()
    full_name = input("Full name: ").strip()
    pw1 = getpass.getpass("Password (min 8 chars): ")
    pw2 = getpass.getpass("Confirm password: ")
    if pw1 != pw2:
        print("Passwords do not match.\n"); return None
    try:
        u = CustomerUser(None, email=email, full_name=full_name, role="customer")
        u.set_password(pw1)
        with _repo().conn:
            repo.create(u)
        print(f"\nAccount created. Welcome, {u.full_name} (customer).\n")
        return u
    except (RepoError, DomainError) as e:
        print(f"\nCould not create account: {e}\n"); return None

def login_or_signup(max_attempts: int = 3) -> User | None:
    while True:
        print("\n========== Authentication ==========")
        print(" 1) Login")
        print(" 2) Sign up")
        print(" 0) Quit")
        print("====================================\n")
        choice = input("Choose: ").strip()
        if choice == "1":
            user = login_flow(max_attempts=max_attempts)
            if user: return user
        elif choice == "2":
            user = signup_flow()
            if user: return user
        elif choice == "0":
            return None
        else:
            print("Please choose a valid option.\n")

# ────────────────────────────────────────────────────────────────────────────────
# Self-service profile (only my own record)
# ────────────────────────────────────────────────────────────────────────────────
def profile_menu(user: User):
    repo = UserRepo()
    while True:
        me = repo.get_by_id(user.id) or user
        print("\n========== My Account ==========")
        print(f" Email : {me.email}")
        print(f" Name  : {me.full_name}")
        print(f" Role  : {me.role}")
        print("--------------------------------")
        print(" 1) Change full name")
        print(" 2) Change email")
        print(" 3) Change password")
        print(" 0) Back")
        print("================================\n")
        choice = input("Choose: ").strip()
        if choice == "1":
            new_name = input("New full name: ").strip()
            if not new_name: print("No change.\n"); continue
            try:
                me.full_name = new_name
                with _repo().conn: repo.save_profile(me)
                print("Name updated.\n")
            except (RepoError, DomainError) as e:
                print(f"Error: {e}\n")
        elif choice == "2":
            new_email = input("New email: ").strip().lower()
            if not new_email: print("No change.\n"); continue
            try:
                me.email = new_email
                with _repo().conn: repo.save_profile(me)
                print("Email updated.\n")
            except (RepoError, DomainError) as e:
                print(f"Error: {e}\n")
        elif choice == "3":
            pw1 = getpass.getpass("New password (min 8 chars): ")
            pw2 = getpass.getpass("Confirm password: ")
            if pw1 != pw2: print("Passwords do not match.\n"); continue
            try:
                me.set_password(pw1)
                with _repo().conn: repo.save_password(me)
                print("Password updated.\n")
            except DomainError as e:
                print(f"Error: {e}\n")
        elif choice == "0":
            return
        else:
            print("Choose a valid option.\n")

# ────────────────────────────────────────────────────────────────────────────────
# Admin: Users maintenance submenu (class-based)
# ────────────────────────────────────────────────────────────────────────────────
def users_admin_menu():
    repo = UserRepo()
    while True:
        print("\n========== Users Maintenance ==========")
        print(" 1) Add user")
        print(" 2) Search users")
        print(" 3) Edit user (email/name/role)")
        print(" 4) Delete user")
        print(" 5) Reset user password")
        print(" 0) Back")
        print("======================================\n")
        choice = input("Choose: ").strip()

        if choice == "0":
            print("\nBack to main menu.\n"); return

        elif choice == "1":  # Add
            try:
                email = input("Email: ").strip().lower()
                name  = input("Full name: ").strip()
                role  = (input("Role [customer|admin] (default customer): ").strip().lower() or "customer")
                pwd1  = getpass.getpass("Password: ")
                pwd2  = getpass.getpass("Confirm password: ")
                if pwd1 != pwd2: print("Passwords do not match."); continue
                u = AdminUser(None, email=email, full_name=name, role="admin") if role == "admin" else CustomerUser(None, email=email, full_name=name, role="customer")
                u.set_password(pwd1)
                with _repo().conn: repo.create(u)
                print(f"Created user id={u.id}.")
            except (RepoError, DomainError) as e:
                print(f"Error: {e}")

        elif choice == "2":  # List/search
            role  = (input("Filter role [customer|admin|blank]: ").strip().lower() or None)
            search= (input("Search (email/name, blank=all): ").strip() or None)
            try:
                users = repo.list(role=role, search=search)
                if not users: print("No users."); continue
                print("\nID  | Role     | Email                 | Name")
                print("-----------------------------------------------")
                for u in users:
                    print(f"{u.id:<3} | {u.role:<8} | {u.email:<20} | {u.full_name}")
            except RepoError as e:
                print(f"Error: {e}")

        elif choice == "3":  # Edit
            try:
                uid = int(input("User ID: ").strip())
                u = repo.get_by_id(uid)
                if not u: print("User not found."); continue
                new_email = input(f"New email [{u.email}] (blank keep): ").strip() or None
                new_name  = input(f"New full name [{u.full_name}] (blank keep): ").strip() or None
                new_role  = input(f"New role [{u.role}] [customer|admin|blank keep]: ").strip().lower() or None
                if new_email: u.email = new_email
                if new_name:  u.full_name = new_name
                if new_role:  u.role = new_role
                with _repo().conn: repo.save_profile(u)
                print("Updated.")
            except (ValueError, DomainError, RepoError) as e:
                print(f"Error: {e}")

        elif choice == "4":  # Delete
            try:
                uid = int(input("User ID: ").strip())
                confirm = input(f"Type 'delete' to confirm deleting user {uid}: ").strip().lower()
                if confirm != "delete": print("Cancelled."); continue
                with _repo().conn: n = repo.delete(uid)
                print("Deleted." if n else "User not found.")
            except Exception as e:
                print(f"Cannot delete: {e}")

        elif choice == "5":  # Reset password
            try:
                uid = int(input("User ID: ").strip())
                u = repo.get_by_id(uid)
                if not u: print("User not found."); continue
                pw1 = getpass.getpass("New password: ")
                pw2 = getpass.getpass("Confirm password: ")
                if pw1 != pw2: print("Passwords do not match."); continue
                u.set_password(pw1)
                with _repo().conn: repo.save_password(u)
                print("Password updated.")
            except (DomainError, RepoError) as e:
                print(f"Error: {e}")

        else:
            print("Choose a valid option.")

# --- Non-interactive services (no input/getpass) ---

def auth_signup(email: str, full_name: str, password: str, *, role: str = "customer") -> User:
    repo = UserRepo()
    u = AdminUser(None, email=email, full_name=full_name, role="admin") if role == "admin" else CustomerUser(None, email=email, full_name=full_name, role="customer")
    u.set_password(password)
    with _repo().conn:
        repo.create(u)
    return u

def auth_login(email: str, password: str) -> User | None:
    repo = UserRepo()
    u = repo.get_by_email(email.strip().lower())
    return u if (u and u.verify_password(password)) else None

def profile_update(user_id: int, *, email: str | None = None, full_name: str | None = None, role: str | None = None) -> int:
    repo = UserRepo()
    u = repo.get_by_id(user_id)
    if not u:
        raise RepoError("User not found.")
    if email is not None: u.email = email
    if full_name is not None: u.full_name = full_name
    if role is not None: u.role = role
    with _repo().conn:
        return repo.save_profile(u)

def password_update(user_id: int, new_password: str) -> int:
    repo = UserRepo()
    u = repo.get_by_id(user_id)
    if not u:
        raise RepoError("User not found.")
    u.set_password(new_password)
    with _repo().conn:
        return repo.save_password(u)
