"""Order processing logic for testing RAG retrieval."""

from calculator import calculate_total, divide


class OrderProcessor:
    """Handles order creation and processing."""

    def __init__(self, discount_rate: float = 0.0):
        self.discount_rate = discount_rate
        self.orders = []

    def create_order(self, item: str, price: float, quantity: int) -> dict:
        """Create a new order and compute the final price."""
        gross = calculate_total(price, quantity)
        discount = gross * self.discount_rate
        net = gross - discount
        order = {"item": item, "gross": gross, "discount": discount, "net": net}
        self.orders.append(order)
        return order

    def average_order_value(self) -> float:
        """Return average net value across all orders."""
        if not self.orders:
            raise ValueError("No orders have been placed yet")
        total = sum(o["net"] for o in self.orders)
        return divide(total, len(self.orders))

    def apply_bulk_discount(self, threshold: int) -> None:
        """Apply an extra 5% discount if order count exceeds threshold."""
        if len(self.orders) > threshold:
            for order in self.orders:
                order["net"] *= 0.95
