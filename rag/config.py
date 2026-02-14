"""Constants and configuration for the codebase RAG system."""

# Qdrant
COLLECTION_NAME = "codebase"
VECTOR_SIZE = 1536
BATCH_SIZE = 64  # points per upsert batch

# OpenAI models
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o"
CHAT_TEMPERATURE = 0.2

# Indexing — directories to skip
SKIP_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules",
    ".idea", ".vscode", "build", "dist", "target", ".gradle",
    ".pytest_cache", ".mypy_cache", ".tox", "eggs", ".eggs",
}

# File extensions to index
PYTHON_EXTENSIONS = {".py"}
JAVA_EXTENSIONS = {".java"}

# Retrieval
TOP_K_SEMANTIC = 10   # results per semantic search
TOP_K_FINAL = 15      # final chunks returned to explainer

# Scoring weights
SCORE_EXACT_FUNCTION = 10
SCORE_EXACT_CLASS = 5
SCORE_EXACT_FILE = 3
SCORE_LINE_MATCH = 8
SCORE_SEMANTIC_MULTIPLIER = 5

# Max log length passed to semantic search
MAX_LOG_CHARS_SEMANTIC = 4000
