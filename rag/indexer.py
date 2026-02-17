"""
Orchestrate: discover files → chunk → embed → upsert to Qdrant.
Also creates the collection and payload indexes if they don't exist.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Iterator

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    KeywordIndexParams,
    IntegerIndexParams,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from rag.chunker import chunk_file
from rag.config import (
    BATCH_SIZE,
    COLLECTION_NAME,
    JAVA_EXTENSIONS,
    PYTHON_EXTENSIONS,
    SKIP_DIRS,
    VECTOR_SIZE,
)
from rag.embedder import embed_texts

load_dotenv()


# ---------------------------------------------------------------------------
# Qdrant setup
# ---------------------------------------------------------------------------

def _qdrant_client() -> QdrantClient:
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")
    if not url:
        raise EnvironmentError("QDRANT_URL is not set in .env")
    return QdrantClient(url=url, api_key=api_key)


def ensure_collection(client: QdrantClient) -> None:
    """Create the collection and all payload indexes if they don't exist."""
    existing = {c.name for c in client.get_collections().collections}
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        print(f"[indexer] Created collection '{COLLECTION_NAME}'")
    else:
        print(f"[indexer] Collection '{COLLECTION_NAME}' already exists")

    # KEYWORD indexes
    keyword_fields = [
        "file_path", "file_name", "language", "chunk_type",
        "function_name", "class_name", "package",
    ]
    for field in keyword_fields:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name=field,
            field_schema=PayloadSchemaType.KEYWORD,
        )

    # INTEGER indexes for line numbers
    for field in ("line_start", "line_end"):
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name=field,
            field_schema=PayloadSchemaType.INTEGER,
        )

    print("[indexer] Payload indexes ensured.")


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def _discover_files(root: str) -> Iterator[str]:
    """Walk root recursively, yielding .py and .java file paths."""
    allowed = PYTHON_EXTENSIONS | JAVA_EXTENSIONS
    for path in Path(root).rglob("*"):
        if path.is_file() and path.suffix.lower() in allowed:
            # Skip excluded directories anywhere in the path
            parts = set(path.parts)
            if parts & SKIP_DIRS:
                continue
            yield str(path)


# ---------------------------------------------------------------------------
# Point ID
# ---------------------------------------------------------------------------

_UUID5_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def _chunk_id(chunk: dict) -> str:
    key = "|".join([
        chunk["file_path"],
        chunk["chunk_type"],
        chunk["function_name"],
        chunk["class_name"],
        str(chunk["line_start"]),
    ])
    return str(uuid.uuid5(_UUID5_NAMESPACE, key))


# ---------------------------------------------------------------------------
# Embed text construction
# ---------------------------------------------------------------------------

def _embed_text(chunk: dict) -> str:
    """Build the text that gets embedded for a chunk."""
    header = (
        f"# file: {chunk['file_path']}"
        f" | class: {chunk['class_name'] or 'N/A'}"
        f" | function: {chunk['function_name'] or 'N/A'}\n"
    )
    return header + chunk["source"]


# ---------------------------------------------------------------------------
# Index a directory
# ---------------------------------------------------------------------------

def index_directory(root: str) -> None:
    client = _qdrant_client()
    ensure_collection(client)

    all_chunks: list[dict] = []
    files_processed = 0

    print(f"[indexer] Discovering files under '{root}' ...")
    for file_path in _discover_files(root):
        chunks = chunk_file(file_path)
        if chunks:
            all_chunks.extend(chunks)
            files_processed += 1

    print(f"[indexer] Found {files_processed} files → {len(all_chunks)} chunks.")
    if not all_chunks:
        print("[indexer] Nothing to index.")
        return

    # Embed and upsert in batches
    total_upserted = 0
    for batch_start in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[batch_start : batch_start + BATCH_SIZE]
        texts = [_embed_text(c) for c in batch]
        vectors = embed_texts(texts)

        points = [
            PointStruct(
                id=_chunk_id(c),
                vector=vec,
                payload={
                    "file_path": c["file_path"],
                    "file_name": c["file_name"],
                    "language": c["language"],
                    "chunk_type": c["chunk_type"],
                    "function_name": c["function_name"],
                    "class_name": c["class_name"],
                    "package": c["package"],
                    "line_start": c["line_start"],
                    "line_end": c["line_end"],
                    "source": c["source"],
                },
            )
            for c, vec in zip(batch, vectors)
        ]

        client.upsert(collection_name=COLLECTION_NAME, points=points)
        total_upserted += len(points)
        print(
            f"[indexer]  Upserted batch {batch_start // BATCH_SIZE + 1}"
            f" ({total_upserted}/{len(all_chunks)} chunks)"
        )

    print(f"[indexer] Done. {total_upserted} chunks indexed into '{COLLECTION_NAME}'.")
