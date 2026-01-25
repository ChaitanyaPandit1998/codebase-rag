"""A simple calculator module for testing the RAG application."""


class Calculator:
    """A basic calculator class with common mathematical operations."""

    def __init__(self):
        """Initialize the calculator."""
        self.history = []

    def add(self, a: float, b: float) -> float:
        """
        Add two numbers together.

        Args:
            a: First number
            b: Second number

        Returns:
            Sum of a and b
        """
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result

    def subtract(self, a: float, b: float) -> float:
        """
        Subtract b from a.

        Args:
            a: Number to subtract from
            b: Number to subtract

        Returns:
            Difference of a and b
        """
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result

    def multiply(self, a: float, b: float) -> float:
        """
        Multiply two numbers.

        Args:
            a: First number
            b: Second number

        Returns:
            Product of a and b
        """
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result

    def divide(self, a: float, b: float) -> float:
        """
        Divide a by b.

        Args:
            a: Numerator
            b: Denominator

        Returns:
            Quotient of a and b

        Raises:
            ValueError: If b is zero
        """
        if b == 0:
            raise ValueError("Cannot divide by zero")

        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        return result

    def get_history(self) -> list:
        """
        Get the calculation history.

        Returns:
            List of calculation strings
        """
        return self.history.copy()

    def clear_history(self):
        """Clear the calculation history."""
        self.history = []


def calculate_total(items: list) -> float:
    """
    Calculate the total sum of a list of numbers.

    Args:
        items: List of numbers to sum

    Returns:
        Total sum of all items, or None if list is empty
    """
    if not items:
        return None

    total = sum(items)
    return total


def process_payment(amount: float, payment_method: str = "credit_card") -> dict:
    """
    Process a payment transaction.

    This function simulates payment processing with different payment methods.
    It includes basic validation and returns a transaction result.

    Args:
        amount: Payment amount (must be positive)
        payment_method: Method of payment (credit_card, debit_card, paypal)

    Returns:
        Dictionary with transaction details including status and transaction_id

    Raises:
        ValueError: If amount is negative or zero
        ValueError: If payment_method is not supported
    """
    if amount <= 0:
        raise ValueError("Payment amount must be positive")

    valid_methods = ["credit_card", "debit_card", "paypal"]
    if payment_method not in valid_methods:
        raise ValueError(f"Payment method must be one of {valid_methods}")

    # Simulate transaction
    transaction = {
        "status": "success",
        "amount": amount,
        "method": payment_method,
        "transaction_id": f"TXN_{hash(amount + len(payment_method))}",
        "message": "Payment processed successfully"
    }

    return transaction
