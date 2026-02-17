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

### Generate a test log

```
$ python main.py generate-log
[generate-log] Written 12 lines to test.log
```

Runs `test_codebase/run_scenario.py` as a subprocess and captures its output (stdout + stderr) to `test.log`. An optional positional argument overrides the destination path:

```
$ python main.py generate-log my_run.log
[generate-log] Written 12 lines to my_run.log
```

### Explain a log file

```
$ python main.py explain test.log
[explain] Retrieving relevant code chunks ...
[explain] Retrieved 15 chunks. Calling GPT-4o ...

============================================================
## Execution Flow Analysis

### Python Order Processing Scenario

1. **Initialization and Order Creation**
   - The `main` function in `run_scenario.py` (line 63) begins by initializing an `OrderProcessor` with a `discount_rate` of 0.10 (lines 9–11 in `order_processor.py`).
   - Two orders are created using `create_order` (lines 13–20 in `order_processor.py`):
     - **Order 1**: "Widget" with a gross price of 32.37, discount of 3.24, and net price of 29.13.
     - **Order 2**: "Gadget" with a gross price of 107.98, discount of 10.80, and net price of 97.18.
   - These orders are logged as created.

2. **Bulk Discount Application**
   - The `apply_bulk_discount` method (lines 29–33 in `order_processor.py`) is called with a threshold of 1.
   - Since there are 2 orders, which exceeds the threshold, a 5% discount is applied to each order's net price.

3. **ZeroDivisionError**
   - The log indicates an attempt to divide an order total by zero, specifically for "Thingamajig".
   - This triggers a `ZeroDivisionError` in the `divide` function (lines 16–20 in `calculator.py`) because the divisor is zero.
   - The error is caught and logged.

4. **ValueError on Empty Processor**
   - An attempt to compute the average order value on an empty `OrderProcessor` instance results in a `ValueError` (lines 22–27 in `order_processor.py`).
   - This is because the `average_order_value` method checks if there are no orders and raises an error if true.

### Java Inventory Scenario

1. **Stock Management**
   - The `main` method in `RunInventory.java` (lines 20–79) starts by adding stock for "Widget" and "Gadget".
   - The `addStock` method (lines 13–15 in `Inventory.java`) updates the stock map.

2. **Stock Reservation**
   - The `reserveStock` method (lines 21–29 in `Inventory.java`) successfully reserves stock for "Widget".
   - An attempt to reserve more stock than available for "Gadget" triggers an `IllegalStateException`, which is logged.

3. **Inventory Value Calculation**
   - The `calculateInventoryValue` method (lines 31–41 in `Inventory.java`) calculates the total inventory value based on provided prices.
   - When calculating with incomplete prices (missing "Sprocket"), an `IllegalArgumentException` is thrown and logged.

## Root Cause Analysis

- **ZeroDivisionError**: The error occurs because the `divide` function is called with a divisor of zero, which is not handled in the `main` function of `run_scenario.py`. The specific order causing this is not detailed in the log, but the error message indicates an attempt to divide 27.674297999999993 by zero.

- **ValueError**: The error arises when attempting to compute the average order value on an empty `OrderProcessor`. This is expected behavior as the method explicitly raises an error if no orders exist.

- **IllegalStateException**: This occurs in the Java inventory scenario when attempting to reserve more stock than available for "Gadget". The `reserveStock` method correctly identifies insufficient stock and throws an exception.

- **IllegalArgumentException**: This is due to missing price information for "Sprocket" during inventory value calculation. The `calculateInventoryValue` method requires all products to have a price, and the absence of a price for "Sprocket" triggers the exception.

## Recommendations

- **ZeroDivisionError**: Ensure that the divisor is checked before calling the `divide` function to prevent division by zero.
- **ValueError**: Consider adding a check or a default return value for the average order value when no orders exist to avoid raising an exception.
- **Java Exceptions**: Ensure that stock levels are checked before attempting reservations and that all products have associated prices before calculating inventory values.
============================================================
```

## Architecture

### Overview

`qdrant-rag` is a CLI tool with three commands — `index`, `generate-log`, and `explain` — that orchestrate a pipeline of five modules: Chunker, Embedder, Indexer, Retriever, and Explainer.

### Component Diagram

```
index command:
  Source Files → Chunker → Embedder → Qdrant (upsert)

explain command:
  Log File → Retriever ──┬── 1. Exact metadata match (function/class/file)
                         ├── 2. Line-number range lookup
                         ├── 3. Semantic search on error messages
                         └── 4. Semantic search on full log text
                              ↓
                         Ranked Chunks → Explainer (GPT-4o) → Analysis
```

### Components

#### 1. CLI Entry Point (`main.py`)

- `argparse` with `index`, `generate-log`, and `explain` subcommands
- `index`: dispatches to `rag.indexer.index_directory()`
- `generate-log`: runs `test_codebase/run_scenario.py` as a subprocess, captures stdout+stderr to `test.log` (or a custom path)
- `explain`: calls `rag.retriever.retrieve()` then `rag.explainer.explain()`

#### 2. Chunker (`rag/chunker.py`)

Uses AST-based chunking rather than naive fixed-size text splitting, preserving semantic boundaries:

- **Python**: uses the `ast` module to extract classes, methods, top-level functions, and module-level code blocks
- **Java**: uses `javalang` to extract classes/interfaces and methods/constructors via brace-matching

Each chunk carries metadata: `file_path`, `language`, `chunk_type`, `function_name`, `class_name`, `package`, `line_start`, `line_end`, `source`.

#### 3. Embedder (`rag/embedder.py`)

- Wraps OpenAI `text-embedding-3-small` (1536 dimensions)
- `embed_texts()` for batch embedding during indexing
- `embed_one()` for single query embedding during retrieval
- Prepends a metadata header to source text before embedding for richer context

#### 4. Indexer (`rag/indexer.py`)

Orchestrates the full indexing pipeline:

1. Discover `.py` and `.java` files (skipping dirs like `.git`, `__pycache__`, `node_modules`, etc.)
2. Chunk each file with the Chunker
3. Batch-embed chunks (batch size: 64) with the Embedder
4. Upsert into Qdrant with cosine distance

Creates the Qdrant collection with payload indexes (keyword indexes on `function_name`, `class_name`, `file_path`; integer indexes on `line_start`, `line_end`) required for filtered search. Uses deterministic UUID5 IDs for idempotent upserts.

#### 5. Retriever (`rag/retriever.py`)

Parses log text with regex patterns for Python tracebacks and Java stack traces, then runs four search strategies in sequence:

| Strategy | Method | Score weight |
|---|---|---|
| 1. Exact function match | Scroll with keyword filter | `SCORE_EXACT_FUNCTION = 10` |
| 2. Exact class match | Scroll with keyword filter | `SCORE_EXACT_CLASS = 5` |
| 3. Exact file match | Scroll with keyword filter | `SCORE_EXACT_FILE = 3` |
| 4. Line-number range | Scroll with range filter on `line_start`/`line_end` | `SCORE_LINE_MATCH = 8` |
| 5. Semantic on errors | Vector search on joined error messages | `score × SCORE_SEMANTIC_MULTIPLIER = 5` |
| 6. Semantic on full log | Vector search on truncated log text | `score × SCORE_SEMANTIC_MULTIPLIER = 5` |

Results are deduplicated by point ID, scores are accumulated, and the top `TOP_K_FINAL = 15` chunks are returned.

#### 6. Explainer (`rag/explainer.py`)

- Sends retrieved code chunks + original log text to `gpt-4o`
- System prompt instructs step-by-step execution tracing with code references
- Returns structured analysis with root cause identification

#### 7. Config (`rag/config.py`)

Central constants used across all modules:

| Constant | Value | Purpose |
|---|---|---|
| `COLLECTION_NAME` | `"codebase"` | Qdrant collection |
| `VECTOR_SIZE` | `1536` | Embedding dimensions |
| `BATCH_SIZE` | `64` | Chunks per upsert batch |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI embedding model |
| `CHAT_MODEL` | `gpt-4o` | OpenAI chat model |
| `TOP_K_SEMANTIC` | `10` | Results per semantic search |
| `TOP_K_FINAL` | `15` | Final chunks sent to explainer |

### Key Design Notes

- **Strict filtering**: every payload field used in a filter has a Qdrant payload index — the server rejects filtered queries on un-indexed fields
- **Idempotent indexing**: UUID5 IDs derived from file path + chunk content mean re-indexing the same file updates in place rather than duplicating
- **AST chunking**: preserves function/class boundaries so retrieved chunks map directly to callable units, making GPT-4o's code references more precise
