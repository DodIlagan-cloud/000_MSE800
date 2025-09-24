"""
Week 7 - Activity 4: Singeleton and  Factory design pattern (due date 25 Sep 2025 )
Develop a code to show the usage of both design patterns in your coding for; Design a payment processing system that supports multiple payment methods (e.g., Creditcard, PayPal, Bank Transfer, CryptoPayment, GooglePay).
Use the Factory Design Pattern to create different payment method objects dynamically.
Ensure the payment gateway (the main entry point for processing payments) is implemented as a Singleton, so only one instance of the gateway exists in the system.
Explain your design choices and share your GitHub with code implementation.

- I used Singleton class to ensure that there will only be one instance of connection as the Payment Gateway. It will be 1 thread all through out the shole session. 
- The ABC was used in order to standardize the classes that will be used as the Payment Method. I used just 1 script for this demo, however, I realized that this could be multiple python script from 
where the abstract class and concrete classes are stored. This would ensure that whenever a change is due to the payment methods it is strictly only on their code. This would be a good practice
to maintain the code and ensure that the script only does one thing. 
I know of this method as Modularity, but since I have been learning names of OOP principlesd, I looked it up and there are terms such as 
Separation of Concerns (SoC) and Single Responsibility Principle (SRP) which I would like to adhere to for other complex projects.
 
 
W7A4-SingletonFactory - Week 7 Activity 4 - W3A6 - EJI
Eduardo JR Ilagan
"""


from __future__ import annotations # learned what annotations. type annotations no longer needs quotes
from abc import ABC, abstractmethod
from dataclasses import dataclass # learned what a decorator is and how to make the class immutable by using frozen
from typing import Any, Dict,Type, Callable # learned what hint annotaions are and how it can be used for better coding.
import uuid   # learned what this module is for, use to crate unique IDs
import time   # module that is used to work on time related tasks.
import threading

# ────────────────────────────────────────────────────────────────────────────────
# Singleton for Payment Gateway
# ────────────────────────────────────────────────────────────────────────────────

class _S(type):
    """Thread-safe Singleton metaclass (double-checked locking)."""
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(_S, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class PaymentGateway(metaclass=_S):
    """Main entry point for payments. Only one instance exists."""
    def __init__(self, name: str = "MainGateway") -> None:
        self.name = name

    def process(self, req: PaymentRequest) -> Receipt:
        """
        Orchestrates a full payment:
        1) Build the right PaymentMethod via Factory
        2) authorize() → capture()
        3) Return the final Receipt
        """
        try:
            method = PaymentFactory.create(req.method, req.amount, req.currency, req.metadata)
            auth = method.authorize()
            if auth.status != "authorized":
                return Receipt(
                    payment_id=auth.payment_id,
                    status="failed",
                    method=req.method,
                    amount=req.amount,
                    currency=req.currency,
                    message=f"Authorization failed: {auth.message}",
                )
            cap = method.capture(auth.payment_id)
            return cap
        except Exception as e:
            # Defensive: convert unexpected errors into a failed receipt
            return Receipt(
                payment_id="",
                status="failed",
                method=req.method,
                amount=req.amount,
                currency=req.currency,
                message=f"Gateway error: {e}",
            )

# ────────────────────────────────────────────────────────────────────────────────
# Class for Facotory at PaymentRequests
# classes are frozen to be immutable.
# ────────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class PaymentRequest:
    method: str                # e.g., "creditcard", "paypal", "bank_transfer", "crypto", "googlepay"
    amount: float
    currency: str              # "NZD", "USD", etc.
    metadata: Dict[str, Any]   # method-specific fields (card details, wallet id, etc.)

@dataclass(frozen=True)
class Receipt:
    payment_id: str
    status: str                # "authorized", "captured", "failed"
    method: str
    amount: float
    currency: str
    message: str = ""

# ────────────────────────────────────────────────────────────────────────────────
# Abstract Class Template for Payment Method
# ────────────────────────────────────────────────────────────────────────────────
class PaymentMethod(ABC):
    """Common interface all payment methods must implement."""

    def __init__(self, amount: float, currency: str, metadata: Dict[str, Any]) -> None:
        self.amount = amount
        self.currency = currency
        self.metadata = metadata

    @abstractmethod
    def authorize(self) -> Receipt:
        """Reserve/authorize funds or create a payable intent."""
        raise NotImplementedError

    @abstractmethod
    def capture(self, authorization_id: str) -> Receipt:
        """Settle the previously authorized payment."""
        raise NotImplementedError

    # Shared guard for all methods
    def _require_positive_amount(self) -> None:
        if self.amount <= 0:
            raise ValueError("Amount must be positive.")
        

# ────────────────────────────────────────────────────────────────────────────────
# Factory for Payment Method
# ────────────────────────────────────────────────────────────────────────────────
class PaymentFactory:
    """Creates payment-method objects dynamically based on a method name."""
    _registry: Dict[str, Type[PaymentMethod]] = {}

    @staticmethod
    def _norm(name: str) -> str:
        # normalize: lowercase, remove spaces/underscores/hyphens
        return name.lower().replace(" ", "").replace("_", "").replace("-", "")

    @classmethod
    def register(cls, method_name: str) -> Callable[[Type[PaymentMethod]], Type[PaymentMethod]]:
        """Decorator to register new payment classes: @PaymentFactory.register('creditcard')."""
        def _inner(klass: Type[PaymentMethod]) -> Type[PaymentMethod]:
            cls._registry[cls._norm(method_name)] = klass
            return klass
        return _inner

    @classmethod
    def add(cls, method_name: str, klass: Type[PaymentMethod]) -> None:
        """Alternate non-decorator way to register."""
        cls._registry[cls._norm(method_name)] = klass

    @classmethod
    def create(cls, method_name: str, amount: float, currency: str, metadata: Dict[str, Any]) -> PaymentMethod:
        key = cls._norm(method_name)
        klass = cls._registry.get(key)
        if not klass:
            known = ", ".join(sorted(cls._registry.keys()))
            raise ValueError(f"Unknown payment method '{method_name}'. Known: {known or '(none registered)'}")
        return klass(amount=amount, currency=currency, metadata=metadata)
    
# ────────────────────────────────────────────────────────────────────────────────
# Concrete classes that were added. I built this demo to be within the script. 
# I think real life application would be different as this would be coming from a different file.
# ────────────────────────────────────────────────────────────────────────────────
@PaymentFactory.register("creditcard")    # Registers the class with a decorator as the class is within the same script, this will be a cleaner approach.
class CreditCardPayment(PaymentMethod):
    def authorize(self) -> Receipt:
        # check amount > 0
        self._require_positive_amount()

        # very basic card validation
        card = self.metadata.get("card_number", "")
        if len(card) < 12:
            raise ValueError("Invalid card number")

        # simulate an authorization ID
        auth_id = f"AUTH-CC-{uuid.uuid4()}" ## this is where the uuid was used in order to simulate a generated unique ID

        return Receipt(
            payment_id=auth_id,
            status="authorized",
            method="creditcard",
            amount=self.amount,
            currency=self.currency,
            message="Credit card authorized successfully."
        )

    def capture(self, authorization_id: str) -> Receipt:
        # simulate processing time
        time.sleep(0.1)

        return Receipt(
            payment_id=f"CAP-CC-{uuid.uuid4()}",
            status="captured",
            method="creditcard",
            amount=self.amount,
            currency=self.currency,
            message=f"Captured authorization {authorization_id}."
        )

@PaymentFactory.register("paypal")    
class PayPalPayment(PaymentMethod):
    def authorize(self) -> Receipt:
        self._require_positive_amount()
        account = self.metadata.get("paypal_account")
        if not account:
            raise ValueError("Missing PayPal account")

        auth_id = f"AUTH-PP-{uuid.uuid4()}"
        return Receipt(
            payment_id=auth_id,
            status="authorized",
            method="paypal",
            amount=self.amount,
            currency=self.currency,
            message="PayPal authorization created."
        )

    def capture(self, authorization_id: str) -> Receipt:
        time.sleep(0.05)
        return Receipt(
            payment_id=f"CAP-PP-{uuid.uuid4()}",
            status="captured",
            method="paypal",
            amount=self.amount,
            currency=self.currency,
            message=f"Captured PayPal authorization {authorization_id}."
        )

@PaymentFactory.register("banktransfer")    
class BankTransferPayment(PaymentMethod):
    def authorize(self) -> Receipt:
        self._require_positive_amount()
        account = self.metadata.get("iban") or self.metadata.get("account_no")
        if not account:
            raise ValueError("Missing bank account info")

        auth_id = f"AUTH-BT-{uuid.uuid4()}"
        return Receipt(
            payment_id=auth_id,
            status="authorized",
            method="bank_transfer",
            amount=self.amount,
            currency=self.currency,
            message="Bank transfer instructions issued."
        )

    def capture(self, authorization_id: str) -> Receipt:
        return Receipt(
            payment_id=f"CAP-BT-{uuid.uuid4()}",
            status="captured",
            method="bank_transfer",
            amount=self.amount,
            currency=self.currency,
            message=f"Funds confirmed for {authorization_id}."
        )

@PaymentFactory.register("crypto")    
class CryptoPayment(PaymentMethod):
    def authorize(self) -> Receipt:
        self._require_positive_amount()
        wallet = self.metadata.get("walletaddr")
        if not wallet:
            raise ValueError("Missing wallet address")

        auth_id = f"AUTH-CR-{uuid.uuid4()}"
        return Receipt(
            payment_id=auth_id,
            status="authorized",
            method="crypto",
            amount=self.amount,
            currency=self.currency,
            message="Awaiting blockchain confirmations."
        )

    def capture(self, authorization_id: str) -> Receipt:
        time.sleep(0.1)
        return Receipt(
            payment_id=f"CAP-CR-{uuid.uuid4()}",
            status="captured",
            method="crypto",
            amount=self.amount,
            currency=self.currency,
            message=f"On-chain confirmations reached for {authorization_id}."
        )

@PaymentFactory.register("googlepay")    
class GooglePayPayment(PaymentMethod):
    def authorize(self) -> Receipt:
        self._require_positive_amount()
        token = self.metadata.get("gpay_token")
        if not token:
            raise ValueError("Missing Google Pay token")

        auth_id = f"AUTH-GP-{uuid.uuid4()}"
        return Receipt(
            payment_id=auth_id,
            status="authorized",
            method="googlepay",
            amount=self.amount,
            currency=self.currency,
            message="Google Pay tokenized authorization."
        )

    def capture(self, authorization_id: str) -> Receipt:
        time.sleep(0.02)
        return Receipt(
            payment_id=f"CAP-GP-{uuid.uuid4()}",
            status="captured",
            method="googlepay",
            amount=self.amount,
            currency=self.currency,
            message=f"Captured Google Pay authorization {authorization_id}."
        )

if __name__ == "__main__":

    pg = PaymentGateway()
    while True:
        
        print("===== Choose the Payment Method =====")
        print(" 1 Cash")
        print(" 2 Credit Card")
        print(" 3 Bank Transfer")
        print(" 4 Paypal")
        print(" 5 Crypto")
        print(" 6 Google Pay")
        print(" 0 Cancel")
        pm = input("Enter Payment Method: ")
        if pm == "1":
            print("Cash Payment Successful.")
        elif pm == "2":
            amt = float(input("Enter Amount: "))
            request = PaymentRequest(
                method="credit-card",          # aliases like "creditcard", "credit_card" also work
                amount=amt,
                currency="NZD",
                metadata={"card_number": "4111111111111111"}
            )
            processor = PaymentFactory.create(request.method, request.amount, request.currency, request.metadata)
            auth = processor.authorize()
            print(auth)
            cap = processor.capture(auth.payment_id)
            print(cap)
            receipt = pg.process(request)
            print(f"[{receipt.method}] {receipt.status.upper()} {receipt.amount} {receipt.currency} :: {receipt.message} (id={receipt.payment_id})")
            print("Credit Card Payment Successful.")
        elif pm == "3":
            amt = float(input("Enter Amount: "))
            request = PaymentRequest(
                method="banktransfer",
                amount=amt,
                currency="NZD",
                metadata={"iban": "123-459-786"} # will be different for each payment method.
            )
            processor = PaymentFactory.create(request.method, request.amount, request.currency, request.metadata)
            auth = processor.authorize()
            print(auth)
            cap = processor.capture(auth.payment_id)
            print(cap)
            print("Bank Transfer Payment Successful.")
        elif pm == "4":
            amt = float(input("Enter Amount: "))
            request = PaymentRequest(
                method="paypal",          # aliases like "creditcard", "credit_card" also work
                amount=amt,
                currency="NZD",
                metadata={"paypal_account": "paypal@account.com"}
            )
            processor = PaymentFactory.create(request.method, request.amount, request.currency, request.metadata)
            auth = processor.authorize()
            print(auth)
            cap = processor.capture(auth.payment_id)
            print(cap)
            receipt = pg.process(request)
            print(f"[{receipt.method}] {receipt.status.upper()} {receipt.amount} {receipt.currency} :: {receipt.message} (id={receipt.payment_id})")
            print("Paypal Payment Successful.")
        elif pm == "5":
            amt = float(input("Enter Amount: "))
            request = PaymentRequest(
                method="crypto",          # aliases like "creditcard", "credit_card" also work
                amount=amt,
                currency="NZD",
                metadata={"walletaddr": "becd-opop-9089-oiui"}
            )
            processor = PaymentFactory.create(request.method, request.amount, request.currency, request.metadata)
            auth = processor.authorize()
            print(auth)
            cap = processor.capture(auth.payment_id)
            print(cap)
            receipt = pg.process(request)
            print(f"[{receipt.method}] {receipt.status.upper()} {receipt.amount} {receipt.currency} :: {receipt.message} (id={receipt.payment_id})")
            print("Crypto Payment Successful.")
        elif pm == "6":
            amt = float(input("Enter Amount: "))
            request = PaymentRequest(
                method="googlepay",          # aliases like "creditcard", "credit_card" also work
                amount=amt,
                currency="NZD",
                metadata={"gpay_token": "user@gmail.com"}
            )
            processor = PaymentFactory.create(request.method, request.amount, request.currency, request.metadata)
            auth = processor.authorize()
            print(auth)
            cap = processor.capture(auth.payment_id)
            print(cap)
            receipt = pg.process(request)
            print(f"[{receipt.method}] {receipt.status.upper()} {receipt.amount} {receipt.currency} :: {receipt.message} (id={receipt.payment_id})")
            print("Google Pay Payment Successful.")
        else:
            print("\nTransaction Cancelled!\n")
            break
