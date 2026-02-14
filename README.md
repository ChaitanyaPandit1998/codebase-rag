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

## Architecture

### Overview

`qdrant-rag` is a CLI tool with two commands — `index` and `explain` — that orchestrate a pipeline of five modules: Chunker, Embedder, Indexer, Retriever, and Explainer.

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

- `argparse` with `index` and `explain` subcommands
- `index`: dispatches to `rag.indexer.index_directory()`
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
