"""Functions, classes, decorators and lambdas."""
from dataclasses import dataclass
from typing import Optional


def greet(name: str, greeting: str = "Hello", *args, **kwargs) -> str:
    """Return a greeting."""
    return f"{greeting}, {name}!"


def factorial(n):
    return 1 if n <= 1 else n * factorial(n - 1)


square = lambda value: value ** 2


class Account:
    interest_rate = 0.05

    def __init__(self, owner, balance=0.0):
        self.owner = owner
        self._balance = balance

    @property
    def balance(self):
        return self._balance

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deposit must be positive")
        self._balance += amount

    @staticmethod
    def describe() -> str:
        return 'An account'


@dataclass
class Point:
    x: int = 0
    y: int = 0
    label: Optional[str] = None


def outer():
    counter = 0

    def inner():
        nonlocal counter
        counter += 1
        return counter

    return inner


async def fetch(url):
    await download(url)
    return url
