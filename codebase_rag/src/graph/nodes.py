"""Node functions for the LangGraph workflow."""
import os
from typing import Any, Dict
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from .state import GraphState


def get_llm():
    """Get the LLM instance."""
    model_name = os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')
    return ChatOpenAI(model=model_name, temperature=0)


def retrieve(state: GraphState, retriever) -> Dict[str, Any]:
    """
    Retrieve relevant documents from the vector store.

    Args:
        state: Current graph state
        retriever: Vector store retriever

    Returns:
        Updated state with retrieved documents
    """
    print(f"---RETRIEVE---")
    question = state["question"]

    # Retrieve documents
    documents = retriever.invoke(question)

    print(f"Retrieved {len(documents)} documents")

    return {"documents": documents, "question": question}


def grade_documents(state: GraphState) -> Dict[str, Any]:
    """
    Grade retrieved documents for relevance.

    Args:
        state: Current graph state

    Returns:
        Updated state with relevance score
    """
    print("---GRADE DOCUMENTS---")

    question = state["question"]
    documents = state["documents"]

    # Grading prompt
    grading_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a grader assessing relevance of retrieved code documents to a user question.

If the document contains code or information related to the user question, grade it as relevant.
Give a binary score 'yes' or 'no' to indicate whether the document is relevant to the question.

Respond with only 'yes' or 'no'."""),
        ("human", "Question: {question}\n\nDocument:\n{document}")
    ])

    llm = get_llm()
    chain = grading_prompt | llm | StrOutputParser()

    # Score each document
    filtered_docs = []
    for doc in documents:
        score = chain.invoke({
            "question": question,
            "document": doc.page_content
        })

        grade = score.strip().lower()
        if grade == "yes":
            print(f"  RELEVANT: {doc.metadata.get('relative_path', 'unknown')}")
            filtered_docs.append(doc)
        else:
            print(f"  NOT RELEVANT: {doc.metadata.get('relative_path', 'unknown')}")

    # Determine overall relevance
    relevance_score = "yes" if filtered_docs else "no"

    print(f"Relevant documents: {len(filtered_docs)}/{len(documents)}")

    return {
        "documents": filtered_docs,
        "question": question,
        "relevance_score": relevance_score
    }


def generate(state: GraphState) -> Dict[str, Any]:
    """
    Generate answer from relevant documents.

    Args:
        state: Current graph state

    Returns:
        Updated state with generated answer
    """
    print("---GENERATE---")

    question = state["question"]
    documents = state["documents"]

    # Format documents
    context = "\n\n".join([
        f"File: {doc.metadata.get('relative_path', 'unknown')}\n{doc.page_content}"
        for doc in documents
    ])

    # Generation prompt
    generation_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert code assistant helping developers understand their codebase.

Use the retrieved code snippets below to answer the user's question. Be specific and reference file names and code when appropriate.

If the code snippets don't contain enough information to fully answer the question, say so and provide the best answer you can based on what's available.

Format your response clearly with:
- Direct answer to the question
- Relevant code references with file paths
- Explanations of how the code works

Retrieved Code:
{context}"""),
        ("human", "{question}")
    ])

    llm = get_llm()
    chain = generation_prompt | llm | StrOutputParser()

    generation = chain.invoke({
        "context": context,
        "question": question
    })

    return {
        "generation": generation,
        "question": question,
        "documents": documents
    }


def transform_query(state: GraphState) -> Dict[str, Any]:
    """
    Transform the query to improve retrieval.

    Args:
        state: Current graph state

    Returns:
        Updated state with rewritten question
    """
    print("---TRANSFORM QUERY---")

    question = state["question"]
    retry_count = state.get("retry_count", 0)

    # Query rewriting prompt
    rewrite_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a question re-writer that converts an input question to a better version optimized for code search.

Look at the initial question and formulate an improved question that will retrieve more relevant code snippets.

Consider:
- Technical terminology and function/class names
- Specific programming concepts
- Clear, focused intent

Respond with only the rewritten question, nothing else."""),
        ("human", "{question}")
    ])

    llm = get_llm()
    chain = rewrite_prompt | llm | StrOutputParser()

    better_question = chain.invoke({"question": question})

    print(f"Original: {question}")
    print(f"Rewritten: {better_question}")

    return {
        "question": better_question,
        "retry_count": retry_count + 1
    }
