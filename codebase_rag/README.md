# LangGraph RAG Application for Codebase Querying

A powerful LangGraph/LangChain RAG (Retrieval-Augmented Generation) application that enables natural language querying of your codebase using self-correcting retrieval with document grading and query rewriting.

## Features

- **Code-Aware Document Loading**: Intelligently loads and processes Python files from your codebase
- **Semantic Search**: Uses OpenAI embeddings and ChromaDB for efficient vector similarity search
- **Self-Correcting Retrieval**: LangGraph workflow with document grading and automatic query rewriting
- **Interactive CLI**: Query your codebase through command-line or interactive mode

## Architecture

The application uses a LangGraph workflow with the following components:

1. **RETRIEVE**: Query ChromaDB for relevant code chunks
2. **GRADE DOCUMENTS**: LLM assesses if retrieved chunks are relevant
3. **GENERATE**: LLM generates answer from relevant context
4. **TRANSFORM QUERY**: Rewrites query for better retrieval (if documents not relevant)

The workflow automatically retries with improved queries if initial results aren't relevant.

## Installation

1. Clone or navigate to this directory:
```bash
cd codebase_rag
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```

4. Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

### 1. Index a Codebase

First, index your codebase to create the vector database:

```bash
python -m app.cli index /path/to/your/codebase
```

Options:
- `--extensions`: File extensions to index (default: `.py`)
- `--chunk-size`: Chunk size for text splitting (default: 1000)
- `--chunk-overlap`: Chunk overlap (default: 200)
- `--db-path`: Custom database path
- `--collection`: Collection name (default: "codebase")

Example:
```bash
python -m app.cli index ../my_project --extensions .py .js .ts
```

### 2. Query the Codebase

Ask questions about your indexed codebase:

```bash
python -m app.cli query "What does the main function do?"
```

Example queries:
- `"How is error handling implemented in API endpoints?"`
- `"What design patterns are used in this codebase?"`
- `"Explain the process_payment function"`
- `"Why might calculate_total return None?"`

### 3. Interactive Mode

Start an interactive session for multiple queries:

```bash
python -m app.cli interactive
```

Type your questions and get answers. Type `exit` or `quit` to end the session.

## Configuration

Configure the application through environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `OPENAI_MODEL` | OpenAI model for generation | `gpt-4-turbo-preview` |
| `EMBEDDING_MODEL` | OpenAI embedding model | `text-embedding-3-small` |
| `CHROMA_DB_PATH` | ChromaDB storage path | `./chroma_db` |
| `CHUNK_SIZE` | Text chunk size | `1000` |
| `CHUNK_OVERLAP` | Chunk overlap size | `200` |
| `TOP_K_DOCUMENTS` | Number of documents to retrieve | `4` |
| `MAX_RETRIES` | Max query rewrite attempts | `2` |

## Project Structure

```
codebase_rag/
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
├── README.md                  # This file
├── src/
│   ├── loader/
│   │   └── code_loader.py     # Load Python files from directory
│   ├── processing/
│   │   └── text_splitter.py   # Code-aware text chunking
│   ├── vectorstore/
│   │   └── chroma_store.py    # ChromaDB vector store operations
│   └── graph/
│       ├── state.py           # GraphState TypedDict definition
│       ├── nodes.py           # Graph node functions
│       └── workflow.py        # LangGraph workflow compilation
└── app/
    └── cli.py                 # Command-line interface
```

## How It Works

1. **Indexing Phase**:
   - Loads code files from the specified directory
   - Splits code into semantic chunks using Python-aware text splitter
   - Generates embeddings using OpenAI's embedding model
   - Stores embeddings in ChromaDB vector database

2. **Query Phase**:
   - User asks a question
   - Retrieves most relevant code chunks from vector database
   - LLM grades each chunk for relevance
   - If relevant: generates answer
   - If not relevant: rewrites query and retrieves again (up to max retries)
   - Returns answer with file references

## Use Cases

- **Code Understanding**: "What does the `process_payment` function do?"
- **Pattern Analysis**: "How is error handling implemented in API endpoints?"
- **Architecture Questions**: "What design patterns are used in this codebase?"
- **Debugging**: "Why might `calculate_total` return None?"
- **Documentation**: "How do I use the authentication module?"

## Example Session

```bash
# Index your codebase
$ python -m app.cli index ./my_project

Loading code files...
Loaded 45 files:
  .py: 45 files
Total characters: 123,456

Splitting documents into chunks...
Created 234 chunks

Creating vector store...
Vector store created at ./chroma_db

# Query it
$ python -m app.cli query "How does authentication work?"

Processing query through LangGraph workflow...

---RETRIEVE---
Retrieved 4 documents
---GRADE DOCUMENTS---
  RELEVANT: src/auth/login.py
  RELEVANT: src/auth/middleware.py
  NOT RELEVANT: src/utils/helpers.py
  RELEVANT: src/models/user.py
Relevant documents: 3/4
---DECISION: DOCUMENTS ARE RELEVANT, GENERATE ANSWER---
---GENERATE---

============================================================
ANSWER
============================================================

Authentication in this codebase is implemented using JWT tokens...

[Detailed answer with code references]

============================================================
Retrieved 3 relevant documents
============================================================
```

## Troubleshooting

**Error: OPENAI_API_KEY not found**
- Make sure you've created a `.env` file with your API key

**Error: Vector store does not exist**
- You need to index a codebase first using the `index` command

**No documents found to index**
- Check that the path is correct and contains files with the specified extensions

## License

MIT
