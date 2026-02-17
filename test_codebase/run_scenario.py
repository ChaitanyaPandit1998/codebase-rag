"""
Runner script for exercising calculator.py and order_processor.py.

Produces realistic log output (INFO + ERROR with tracebacks) that can be
captured into test.log via `python main.py generate-log`.
"""

import logging
import os
import shutil
import subprocess
import sys
import tempfile

# Allow importing sibling modules (calculator, order_processor)
sys.path.insert(0, os.path.dirname(__file__))

from order_processor import OrderProcessor
from calculator import divide

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def run_java_inventory() -> None:
    """Compile and run RunInventory.java, printing its output to stdout."""
    javac = shutil.which("javac")
    java = shutil.which("java")
    if not javac or not java:
        log.warning("Java not found on PATH — skipping Java inventory scenario")
        return

    test_dir = os.path.dirname(__file__)
    inventory_java = os.path.join(test_dir, "Inventory.java")
    run_inventory_java = os.path.join(test_dir, "RunInventory.java")

    with tempfile.TemporaryDirectory() as out_dir:
        compile_result = subprocess.run(
            [javac, "-d", out_dir, inventory_java, run_inventory_java],
            capture_output=True,
            text=True,
        )
        if compile_result.returncode != 0:
            log.error("javac compilation failed:\n%s", compile_result.stderr)
            return

        run_result = subprocess.run(
            [java, "-cp", out_dir, "com.example.shop.RunInventory"],
            capture_output=True,
            text=True,
        )
        if run_result.stdout:
            print(run_result.stdout, end="")
        if run_result.returncode != 0 and run_result.stderr:
            log.error("java RunInventory stderr:\n%s", run_result.stderr)


def main() -> None:
    log.info("Starting order processing scenario")

    processor = OrderProcessor(discount_rate=0.10)

    # Valid orders
    order1 = processor.create_order("Widget", price=9.99, quantity=3)
    log.info("Created order: item=Widget gross=%.2f discount=%.2f net=%.2f",
             order1["gross"], order1["discount"], order1["net"])

    order2 = processor.create_order("Gadget", price=49.99, quantity=2)
    log.info("Created order: item=Gadget gross=%.2f discount=%.2f net=%.2f",
             order2["gross"], order2["discount"], order2["net"])

    log.info("Applying bulk discount (threshold=1)")
    processor.apply_bulk_discount(threshold=1)
    log.info("Bulk discount applied. Orders now: %d", len(processor.orders))

    # Trigger ZeroDivisionError via divide()
    log.info("Attempting to divide order total by quantity=0 (Thingamajig)")
    try:
        result = divide(processor.orders[0]["net"], 0)
        log.info("Division result: %.2f", result)
    except ZeroDivisionError:
        log.exception("ZeroDivisionError while computing per-unit price for Thingamajig")

    # Trigger ValueError via average_order_value() on empty processor
    log.info("Computing average order value on empty processor")
    empty_processor = OrderProcessor()
    try:
        avg = empty_processor.average_order_value()
        log.info("Average order value: %.2f", avg)
    except ValueError:
        log.exception("ValueError computing average_order_value: no orders placed")

    run_java_inventory()
    log.info("Scenario complete")


if __name__ == "__main__":
    main()
