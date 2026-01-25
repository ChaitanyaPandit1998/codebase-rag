"""GraphState definition for the LangGraph workflow."""
from typing import List, TypedDict
from langchain_core.documents import Document


class GraphState(TypedDict):
    """
    Represents the state of the graph.

    Attributes:
        question: The user's question
        documents: List of retrieved code documents
        generation: The generated answer
        relevance_score: Whether documents are relevant ('yes' or 'no')
        retry_count: Number of query rewrite attempts
    """
    question: str
    documents: List[Document]
    generation: str
    relevance_score: str
    retry_count: int
