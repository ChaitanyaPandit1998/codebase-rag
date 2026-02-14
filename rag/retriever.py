"""
Parse log content, run multi-strategy Qdrant search, and return ranked chunks.
"""

from __future__ import annotations

import os
import re
from typing import Any

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchValue,
    Range,
)

from rag.config import (
    COLLECTION_NAME,
    MAX_LOG_CHARS_SEMANTIC,
    SCORE_EXACT_CLASS,
    SCORE_EXACT_FILE,
    SCORE_EXACT_FUNCTION,
    SCORE_LINE_MATCH,
    SCORE_SEMANTIC_MULTIPLIER,
    TOP_K_FINAL,
    TOP_K_SEMANTIC,
)
from rag.embedder import embed_one

load_dotenv()


# ---------------------------------------------------------------------------
# Log parsing
# ---------------------------------------------------------------------------

# Python traceback: File "path/to/foo.py", line 42, in some_function
_PY_FRAME = re.compile(
    r'File "(?P<path>[^"]+)", line (?P<line>\d+), in (?P<func>\S+)'
)

# Java stack trace: at com.example.MyClass.myMethod(MyClass.java:42)
_JAVA_FRAME = re.compile(
    r'at (?P<pkg>[\w$.]+)\.(?P<class>\w+)\.(?P<method>\w+)\((?P<file>\w+\.java):(?P<line>\d+)\)'
)

# Exception/error message lines (Python or Java)
_ERROR_LINE = re.compile(
    r'(?:^|\s)(?:Exception|Error|Traceback|WARN|ERROR|FATAL|SEVERE)[^\n]*',
    re.MULTILINE,
)

# Simple bare function/class mentions
_IDENTIFIER = re.compile(r'\b([A-Z][a-zA-Z0-9_]+|[a-z_][a-zA-Z0-9_]{3,})\b')


class ParsedLog:
    def __init__(self):
        self.functions: list[str] = []
        self.classes: list[str] = []
        self.file_paths: list[str] = []
        self.line_lookups: list[tuple[str, int]] = []  # (file_path, line_no)
        self.error_messages: list[str] = []


def parse_log(log_text: str) -> ParsedLog:
    parsed = ParsedLog()

    # Python frames
    for m in _PY_FRAME.finditer(log_text):
        path = m.group("path")
        line = int(m.group("line"))
        func = m.group("func")
        if path not in parsed.file_paths:
            parsed.file_paths.append(path)
        if func not in ("?", "<module>", "") and func not in parsed.functions:
            parsed.functions.append(func)
        parsed.line_lookups.append((path, line))

    # Java frames
    for m in _JAVA_FRAME.finditer(log_text):
        cls = m.group("class")
        method = m.group("method")
        line = int(m.group("line"))
        java_file = m.group("file")
        if cls not in parsed.classes:
            parsed.classes.append(cls)
        if method not in parsed.functions:
            parsed.functions.append(method)
        # We don't have full path; store just the filename
        if java_file not in parsed.file_paths:
            parsed.file_paths.append(java_file)
        parsed.line_lookups.append((java_file, line))

    # Error messages
    for m in _ERROR_LINE.finditer(log_text):
        msg = m.group(0).strip()
        if msg and msg not in parsed.error_messages:
            parsed.error_messages.append(msg)

    return parsed


# ---------------------------------------------------------------------------
# Qdrant client
# ---------------------------------------------------------------------------

def _qdrant_client() -> QdrantClient:
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")
    if not url:
        raise EnvironmentError("QDRANT_URL is not set in .env")
    return QdrantClient(url=url, api_key=api_key)


# ---------------------------------------------------------------------------
# Search strategies
# ---------------------------------------------------------------------------

def _scroll_filter(client: QdrantClient, flt: Filter, limit: int = 20) -> list[dict]:
    """Run a scroll with a filter and return payload dicts keyed by point id."""
    results = []
    offset = None
    fetched = 0
    while fetched < limit:
        batch_size = min(limit - fetched, 100)
        points, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=flt,
            limit=batch_size,
            with_payload=True,
            with_vectors=False,
            offset=offset,
        )
        for p in points:
            results.append({"id": str(p.id), "payload": p.payload, "score": 0.0})
        fetched += len(points)
        if offset is None:
            break
    return results


def _semantic_search(client: QdrantClient, query_text: str, limit: int) -> list[dict]:
    """Embed query_text and run a vector similarity search."""
    vec = embed_one(query_text)
    hits = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vec,
        limit=limit,
        with_payload=True,
    )
    return [
        {"id": str(p.id), "payload": p.payload, "score": float(p.score)}
        for p in hits.points
    ]


# ---------------------------------------------------------------------------
# Merge and rank
# ---------------------------------------------------------------------------

def _merge_and_rank(
    parsed: ParsedLog,
    exact_hits: list[dict],
    line_hits: list[dict],
    error_hits: list[dict],
    log_hits: list[dict],
) -> list[dict]:
    """Deduplicate by id, compute composite score, return top-k."""
    registry: dict[str, dict] = {}

    def _add(hit: dict, base_score: float = 0.0):
        pid = hit["id"]
        if pid not in registry:
            registry[pid] = {"id": pid, "payload": hit["payload"], "score": base_score}
        else:
            registry[pid]["score"] += base_score

    # Exact metadata hits
    for hit in exact_hits:
        payload = hit["payload"]
        s = 0.0
        fn = payload.get("function_name", "")
        cn = payload.get("class_name", "")
        fp = payload.get("file_path", "")
        if fn and fn in parsed.functions:
            s += SCORE_EXACT_FUNCTION
        if cn and cn in parsed.classes:
            s += SCORE_EXACT_CLASS
        if fp and any(fp.endswith(f) or f.endswith(fp) for f in parsed.file_paths):
            s += SCORE_EXACT_FILE
        _add(hit, s)

    # Line-number hits
    for hit in line_hits:
        _add(hit, SCORE_LINE_MATCH)

    # Semantic hits: weight by similarity score
    for hit in error_hits + log_hits:
        _add(hit, hit["score"] * SCORE_SEMANTIC_MULTIPLIER)

    ranked = sorted(registry.values(), key=lambda x: x["score"], reverse=True)
    return ranked[:TOP_K_FINAL]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def retrieve(log_text: str) -> list[dict]:
    """
    Parse log, run multi-strategy search, return top-k ranked chunks.
    Each returned item: {"id": ..., "payload": {...}, "score": float}
    """
    parsed = parse_log(log_text)
    client = _qdrant_client()

    # Strategy 1: exact metadata matches
    exact_hits: list[dict] = []

    for fn in parsed.functions[:5]:  # limit to avoid too many requests
        flt = Filter(
            must=[FieldCondition(key="function_name", match=MatchValue(value=fn))]
        )
        exact_hits.extend(_scroll_filter(client, flt))

    for cn in parsed.classes[:5]:
        flt = Filter(
            must=[FieldCondition(key="class_name", match=MatchValue(value=cn))]
        )
        exact_hits.extend(_scroll_filter(client, flt))

    for fp in parsed.file_paths[:5]:
        # Match on suffix (file_path stored as full path)
        flt = Filter(
            must=[FieldCondition(key="file_path", match=MatchValue(value=fp))]
        )
        exact_hits.extend(_scroll_filter(client, flt))

    # Strategy 2: line-number lookup
    line_hits: list[dict] = []
    for fp, lineno in parsed.line_lookups[:10]:
        flt = Filter(
            must=[
                FieldCondition(key="file_path", match=MatchValue(value=fp)),
                FieldCondition(key="line_start", range=Range(lte=lineno)),
                FieldCondition(key="line_end", range=Range(gte=lineno)),
            ]
        )
        line_hits.extend(_scroll_filter(client, flt, limit=5))

    # Strategy 3: semantic on error messages
    error_hits: list[dict] = []
    if parsed.error_messages:
        error_query = " ".join(parsed.error_messages[:3])[:MAX_LOG_CHARS_SEMANTIC]
        error_hits = _semantic_search(client, error_query, TOP_K_SEMANTIC)

    # Strategy 4: semantic on full log text
    log_query = log_text[:MAX_LOG_CHARS_SEMANTIC]
    log_hits = _semantic_search(client, log_query, TOP_K_SEMANTIC)

    return _merge_and_rank(parsed, exact_hits, line_hits, error_hits, log_hits)
