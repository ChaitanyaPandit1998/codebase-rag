# qdrant-rag

A codebase RAG (Retrieval-Augmented Generation) tool that indexes your source code into Qdrant and uses it to explain log files with code-grounded analysis.

## Usage

### Index a codebase

```
$ python main.py index ./test_codebase/
[indexer] Created collection 'codebase'
[indexer] Payload indexes ensured.
[indexer] Discovering files under './test_codebase/' ...
[indexer] Found 3 files → 14 chunks.
[indexer]  Upserted batch 1 (14/14 chunks)
[indexer] Done. 14 chunks indexed into 'codebase'.
```

### Explain a log file

```
$ python main.py explain test.log
[explain] Retrieving relevant code chunks ...
[explain] Retrieved 14 chunks. Calling GPT-4o ...

============================================================
## Execution Flow Analysis

### Order Processing Start
- **Log Entry**: `2024-01-15 10:23:45 INFO  Starting order processing batch`
  - The application begins processing a batch of orders.

### Processing Orders
- **Log Entry**: `2024-01-15 10:23:45 INFO  Processing 3 orders for customer C-991`
  - The system is processing three orders for a specific customer.

### Order Creation
- **Log Entry**: `2024-01-15 10:23:46 INFO  Order created: item=Widget price=19.99 quantity=5`
  - An order for 5 Widgets at $19.99 each is successfully created.
  - **Code Reference**: `OrderProcessor.create_order` (lines 13-20 in `order_processor.py`)
    - Calls `calculate_total(price, quantity)` to compute the gross price.
    - Applies any discount based on `self.discount_rate`.
    - Appends the order to `self.orders`.

- **Log Entry**: `2024-01-15 10:23:46 INFO  Order created: item=Gadget price=49.99 quantity=2`
  - An order for 2 Gadgets at $49.99 each is successfully created.
  - Follows the same process as above.

### Error Encountered
- **Log Entry**: `2024-01-15 10:23:47 ERROR Traceback (most recent call last):`
  - An error occurs during the creation of an order for a "Thingamajig".

#### Error Details
- **Code Reference**: `order_processor.py`, line 22
  - The error occurs in the `create_order` method when calling `calculate_total`.
- **Code Reference**: `calculator.py`, line 22
  - In `calculate_total`, the subtotal is calculated as `price * quantity`.
- **Code Reference**: `calculator.py`, line 10
  - The error is a `ZeroDivisionError` raised by the `divide` function.
  - **Root Cause**: The `divide` function is not directly involved in `calculate_total`. The error message suggests a misuse or misinterpretation of the function elsewhere in the code, possibly in a different context or due to a misconfiguration of the `TAX_RATE` or other logic not shown in the provided code.

### Order Processing Failure
- **Log Entry**: `2024-01-15 10:23:47 ERROR Order processing failed for item=Thingamajig`
  - The order for "Thingamajig" could not be processed due to the error.

### Average Order Value Calculation
- **Log Entry**: `2024-01-15 10:23:48 INFO  Attempting average_order_value calculation`
  - The system attempts to calculate the average order value.
- **Log Entry**: `2024-01-15 10:23:48 ERROR ValueError: No orders have been placed yet`
  - **Code Reference**: `order_processor.py`, line 22-27
  - The `average_order_value` method raises a `ValueError` because `self.orders` is empty.
  - **Root Cause**: The error message contradicts the log entries indicating successful order creation. This suggests a potential issue with order persistence or an incorrect state reset between operations.

## Summary and Recommendations
- **ZeroDivisionError**: Investigate the context in which `divide` is called. Ensure that division operations are correctly guarded against zero denominators.
- **Order Persistence**: Verify that orders are correctly appended to `self.orders` and that the state is maintained across operations.
- **Error Handling**: Implement more robust error handling and logging to capture the context of errors more effectively.
- **Testing**: Conduct thorough testing of the order processing logic, especially around edge cases like zero quantities or prices.
============================================================
```
