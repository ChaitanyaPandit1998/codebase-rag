"""LangGraph workflow compilation."""
import os
from typing import Literal
from langgraph.graph import StateGraph, END
from .state import GraphState
from .nodes import retrieve, grade_documents, generate, transform_query


def decide_to_generate(state: GraphState) -> Literal["generate", "transform_query"]:
    """
    Determine whether to generate an answer or transform the query.

    Args:
        state: Current graph state

    Returns:
        Next node to execute
    """
    relevance_score = state.get("relevance_score", "no")
    retry_count = state.get("retry_count", 0)
    max_retries = int(os.getenv("MAX_RETRIES", "2"))

    if relevance_score == "yes":
        # Documents are relevant, generate answer
        print("---DECISION: DOCUMENTS ARE RELEVANT, GENERATE ANSWER---")
        return "generate"
    elif retry_count >= max_retries:
        # Max retries reached, generate with what we have
        print("---DECISION: MAX RETRIES REACHED, GENERATE WITH AVAILABLE DOCS---")
        return "generate"
    else:
        # Documents not relevant, try rewriting the query
        print("---DECISION: DOCUMENTS NOT RELEVANT, TRANSFORM QUERY---")
        return "transform_query"


def create_workflow(retriever):
    """
    Create and compile the LangGraph workflow.

    Args:
        retriever: Vector store retriever

    Returns:
        Compiled workflow
    """
    # Create the graph
    workflow = StateGraph(GraphState)

    # Define nodes
    workflow.add_node("retrieve", lambda state: retrieve(state, retriever))
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("generate", generate)
    workflow.add_node("transform_query", transform_query)

    # Build graph
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "grade_documents")

    # Conditional edge from grade_documents
    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_generate,
        {
            "generate": "generate",
            "transform_query": "transform_query"
        }
    )

    # Edge from transform_query back to retrieve
    workflow.add_edge("transform_query", "retrieve")

    # Edge from generate to END
    workflow.add_edge("generate", END)

    # Compile
    app = workflow.compile()

    return app
