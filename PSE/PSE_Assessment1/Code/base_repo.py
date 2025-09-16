"""
Assessment 1 - Car System - Dod's Cars
PSEASS - EJI
Eduardo JR Ilagan

base_repo.py — Domain Factory ABCs (row→object mapping contracts)

Purpose
- Define minimal Abstract Base Classes that specify how DB rows are converted
  into domain objects (Factory pattern).
- Keep repos swappable/testable: concrete repos accept a factory implementation
  but the contract stays stable.

Design
- Pattern: Abstract Base Class (ABC) + Factory Method
- Scope: Mapping only; no DB calls here (all DB via sql_repo)
- Dependency: TYPE_CHECKING imports to avoid runtime circulars

Use-Case Support (indirect)
- UC-03 View Available Cars            → CarFactoryABC.car_from_row / Maint mapping
- UC-04 Create Booking                 → BookingFactoryABC.booking_from_row
- UC-05 View Booking Status            → BookingFactoryABC.booking_from_row
- UC-06 Calculate Fees (include)       → BookingFactoryABC.charge_from_row
- UC-08 Approve/Reject Booking         → BookingFactoryABC.booking_from_row
- UC-10/11 Record/Complete Maintenance → CarFactoryABC.maintenance_from_row
- UC-13/14 Block/Unblock Car           → CarFactoryABC.maintenance_from_row
- UC-15 Check Maintenance Conflicts    → CarFactoryABC.maintenance_from_row
"""


from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Mapping, Any, TYPE_CHECKING

Row = Mapping[str, Any]

if TYPE_CHECKING:
    # Forward refs for Pylance; no runtime imports -> avoids cycles
    from user_repo import User
    from car_repo import Car, Maint
    from booking_repo import Booking, Charge

class UserFactoryABC(ABC):
    """Factory for constructing User domain objects from DB rows."""
    @abstractmethod
    def user_from_row(self, row: Row) -> "User": ...

class CarFactoryABC(ABC):
    """Factory for constructing Car & Maint domain objects from DB rows."""
    @abstractmethod
    def car_from_row(self, row: Row) -> "Car": ...
    @abstractmethod
    def maintenance_from_row(self, row: Row) -> "Maint": ...

class BookingFactoryABC(ABC):
    """Factory for constructing Booking & Charge domain objects from DB rows."""
    @abstractmethod
    def booking_from_row(self, row: Row) -> "Booking": ...
    @abstractmethod
    def charge_from_row(self, row: Row) -> "Charge": ...
