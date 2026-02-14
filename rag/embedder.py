"""Thin wrapper around OpenAI embeddings."""

from __future__ import annotations

import os
from typing import List

from openai import OpenAI

from rag.config import EMBEDDING_MODEL


def _client() -> OpenAI:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. Add it to .env or export it."
        )
    return OpenAI(api_key=key)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed a list of texts with text-embedding-3-small.
    Returns a list of float vectors (one per input).
    """
    if not texts:
        return []
    client = _client()
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    # Sort by index to preserve order
    return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]


def embed_one(text: str) -> List[float]:
    """Embed a single string and return its vector."""
    return embed_texts([text])[0]
