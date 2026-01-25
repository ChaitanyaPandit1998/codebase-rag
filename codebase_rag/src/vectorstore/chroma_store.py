"""ChromaDB vector store operations."""
import os
from pathlib import Path
from typing import List, Optional
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


class ChromaStore:
    """Wrapper for ChromaDB vector store operations."""

    def __init__(
        self,
        persist_directory: str = None,
        collection_name: str = "codebase",
        embedding_model: str = None
    ):
        """
        Initialize ChromaDB store.

        Args:
            persist_directory: Directory to persist the database
            collection_name: Name of the collection
            embedding_model: OpenAI embedding model name
        """
        self.persist_directory = persist_directory or os.getenv(
            'CHROMA_DB_PATH', './chroma_db'
        )
        self.collection_name = collection_name
        self.embedding_model = embedding_model or os.getenv(
            'EMBEDDING_MODEL', 'text-embedding-3-small'
        )

        # Create persist directory if it doesn't exist
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(model=self.embedding_model)

        # Initialize vector store (will be set in create or load)
        self.vectorstore: Optional[Chroma] = None

    def create(self, documents: List[Document]) -> Chroma:
        """
        Create a new vector store from documents.

        Args:
            documents: List of Document objects to index

        Returns:
            Chroma vector store instance
        """
        print(f"Creating vector store with {len(documents)} documents...")

        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            collection_name=self.collection_name,
            persist_directory=self.persist_directory
        )

        print(f"Vector store created at {self.persist_directory}")
        return self.vectorstore

    def load(self) -> Chroma:
        """
        Load an existing vector store.

        Returns:
            Chroma vector store instance
        """
        if not Path(self.persist_directory).exists():
            raise ValueError(
                f"Vector store does not exist at {self.persist_directory}. "
                "Please create it first using the 'index' command."
            )

        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

        return self.vectorstore

    def query(
        self,
        query: str,
        k: int = None,
        filter: dict = None
    ) -> List[Document]:
        """
        Query the vector store.

        Args:
            query: Query string
            k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of relevant Document objects
        """
        if self.vectorstore is None:
            self.load()

        k = k or int(os.getenv('TOP_K_DOCUMENTS', '4'))

        results = self.vectorstore.similarity_search(
            query=query,
            k=k,
            filter=filter
        )

        return results

    def as_retriever(self, **kwargs):
        """
        Get the vector store as a retriever.

        Args:
            **kwargs: Arguments to pass to as_retriever()

        Returns:
            VectorStoreRetriever instance
        """
        if self.vectorstore is None:
            self.load()

        # Set default k if not provided
        if 'search_kwargs' not in kwargs:
            kwargs['search_kwargs'] = {}
        if 'k' not in kwargs['search_kwargs']:
            kwargs['search_kwargs']['k'] = int(os.getenv('TOP_K_DOCUMENTS', '4'))

        return self.vectorstore.as_retriever(**kwargs)

    def delete_collection(self):
        """Delete the entire collection."""
        if self.vectorstore is not None:
            self.vectorstore.delete_collection()
            print(f"Collection '{self.collection_name}' deleted.")

    def get_stats(self) -> dict:
        """
        Get statistics about the vector store.

        Returns:
            Dictionary with statistics
        """
        if self.vectorstore is None:
            self.load()

        collection = self.vectorstore._collection
        count = collection.count()

        return {
            'collection_name': self.collection_name,
            'document_count': count,
            'persist_directory': self.persist_directory
        }
