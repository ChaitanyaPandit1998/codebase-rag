"""Simple calculator module for testing RAG indexing."""

TAX_RATE = 0.08


def add(a: float, b: float) -> float:
    """Return the sum of a and b."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Return a minus b."""
    return a - b


def divide(a: float, b: float) -> float:
    """Return a divided by b. Raises ZeroDivisionError if b is 0."""
    if b == 0:
        raise ZeroDivisionError(f"Cannot divide {a} by zero")
    return a / b


def calculate_total(price: float, quantity: int) -> float:
    """Return total price including tax."""
    subtotal = price * quantity
    tax = subtotal * TAX_RATE
    return add(subtotal, tax)
