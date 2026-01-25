"""Code-aware text chunking utilities."""
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_text_splitters import Language


def get_code_splitter(
    chunk_size: int = None,
    chunk_overlap: int = None,
    language: Language = Language.PYTHON
) -> RecursiveCharacterTextSplitter:
    """
    Get a code-aware text splitter.

    Args:
        chunk_size: Maximum size of each chunk
        chunk_overlap: Number of characters to overlap between chunks
        language: Programming language for syntax-aware splitting

    Returns:
        RecursiveCharacterTextSplitter configured for code
    """
    # Get defaults from environment or use hardcoded values
    chunk_size = chunk_size or int(os.getenv('CHUNK_SIZE', '1000'))
    chunk_overlap = chunk_overlap or int(os.getenv('CHUNK_OVERLAP', '200'))

    # Create a Python-aware splitter
    splitter = RecursiveCharacterTextSplitter.from_language(
        language=language,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,  # Add character index to metadata
    )

    return splitter


def split_documents(documents, chunk_size: int = None, chunk_overlap: int = None):
    """
    Split documents into chunks.

    Args:
        documents: List of Document objects to split
        chunk_size: Maximum size of each chunk
        chunk_overlap: Number of characters to overlap between chunks

    Returns:
        List of split Document objects
    """
    splitter = get_code_splitter(chunk_size, chunk_overlap)
    split_docs = splitter.split_documents(documents)

    # Add chunk information to metadata
    for i, doc in enumerate(split_docs):
        doc.metadata['chunk_id'] = i

    return split_docs
