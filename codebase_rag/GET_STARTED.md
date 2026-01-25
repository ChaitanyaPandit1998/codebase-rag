# 🚀 Get Started with LangGraph RAG

## What You Got

A complete, production-ready LangGraph RAG application for querying codebases!

**Stats:**
- 📁 17 Python files
- 📝 905 lines of code
- 🔧 7 core modules
- 📚 3 documentation files
- ✅ Test data included

## Quick Start (3 Steps)

### 1. Install
```bash
cd codebase_rag
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 3. Test
```bash
# Verify setup
python verify_setup.py

# Index test data
python -m app.cli index ./test_data

# Ask a question
python -m app.cli query "What does the process_payment function do?"
```

## What It Does

This application lets you ask natural language questions about any Python codebase:

**Example Queries:**
- "What does the main function do?"
- "How is error handling implemented?"
- "What design patterns are used?"
- "Why might calculate_total return None?"

**The Magic:**
1. Loads your code files
2. Splits them into semantic chunks
3. Creates embeddings and stores in ChromaDB
4. Uses LangGraph workflow to:
   - Retrieve relevant code
   - Grade documents for relevance
   - Rewrite query if needed
   - Generate comprehensive answers

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              LANGGRAPH WORKFLOW                          │
│  ┌─────────┐    ┌──────────┐    ┌────────────┐         │
│  │  START  │───►│ RETRIEVE │───►│   GRADE    │         │
│  └─────────┘    └──────────┘    │ DOCUMENTS  │         │
│                      ▲          └─────┬──────┘         │
│                      │                │                 │
│                      │           [Not Relevant]         │
│                      │                ↓                 │
│                      │          ┌───────────┐          │
│                      └──────────│ TRANSFORM │          │
│                                 │   QUERY   │          │
│                                 └───────────┘          │
│                           [Relevant]                    │
│                                ↓                        │
│                          ┌──────────┐                  │
│                          │ GENERATE │──► END           │
│                          └──────────┘                  │
└─────────────────────────────────────────────────────────┘
```

## File Overview

**Core Application:**
```
src/
├── loader/code_loader.py       # Load Python files
├── processing/text_splitter.py # Chunk code intelligently
├── vectorstore/chroma_store.py # Vector database ops
└── graph/
    ├── state.py                # Workflow state definition
    ├── nodes.py                # retrieve, grade, generate, transform
    └── workflow.py             # LangGraph compilation

app/
└── cli.py                      # CLI interface
```

**Documentation:**
- `README.md` - Full documentation
- `QUICKSTART.md` - Quick start guide
- `IMPLEMENTATION_SUMMARY.md` - Technical details
- `GET_STARTED.md` - This file

**Utilities:**
- `verify_setup.py` - Check installation
- `test_data/` - Sample code for testing

## Commands

### Index a codebase
```bash
python -m app.cli index /path/to/code
```

Options:
- `--extensions .py .js .ts` - File types to index
- `--chunk-size 1000` - Chunk size
- `--chunk-overlap 200` - Overlap size
- `--db-path ./my_db` - Custom DB path

### Query
```bash
python -m app.cli query "Your question here"
```

### Interactive Mode
```bash
python -m app.cli interactive
```

Type questions, get answers, repeat. Type `exit` to quit.

## Real-World Usage

### Index Your Project
```bash
python -m app.cli index ~/my_project/src
```

### Ask About It
```bash
python -m app.cli interactive

Question: How does authentication work?
Question: What databases are used?
Question: Explain the payment flow
```

## Configuration

Edit `.env` to customize:

```bash
# Required
OPENAI_API_KEY=sk-your-key-here

# Optional (defaults shown)
OPENAI_MODEL=gpt-4-turbo-preview
EMBEDDING_MODEL=text-embedding-3-small
CHROMA_DB_PATH=./chroma_db
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_DOCUMENTS=4
MAX_RETRIES=2
```

## Verification Steps

**1. Run verification script:**
```bash
python verify_setup.py
```

Should show all ✓ checks passing.

**2. Index test data:**
```bash
python -m app.cli index ./test_data
```

Expected:
- Loaded 2 files
- Created ~10-15 chunks
- Vector store created

**3. Test queries:**
```bash
python -m app.cli query "What does process_payment do?"
python -m app.cli query "How does error handling work?"
python -m app.cli query "Why might calculate_total return None?"
```

All should return relevant answers with code references.

**4. Try interactive:**
```bash
python -m app.cli interactive
```

Ask multiple questions, verify it responds correctly.

## What Makes This Special

✨ **Self-Correcting**: Automatically rewrites queries if results aren't relevant

✨ **Code-Aware**: Understands Python syntax and structure

✨ **Smart Chunking**: Preserves code context across chunks

✨ **Graded Retrieval**: LLM validates relevance before answering

✨ **File References**: Answers include specific file paths

✨ **Extensible**: Easy to add features or file types

## Next Steps

1. ✅ **Verify Setup**: `python verify_setup.py`
2. ✅ **Test It**: Index test_data and run queries
3. 🎯 **Use It**: Index your own project
4. 🔧 **Customize**: Adjust settings in `.env`
5. 🚀 **Extend**: Add new node types or features

## Troubleshooting

**"OPENAI_API_KEY not found"**
- Create `.env` file from `.env.example`
- Add your API key: `OPENAI_API_KEY=sk-...`

**"Vector store does not exist"**
- Run `index` command first
- Check the path is correct

**Import errors**
- Install dependencies: `pip install -r requirements.txt`

**Slow responses**
- Normal - LLM calls take time
- Consider using a faster model in `.env`

## Need Help?

Check the documentation:
1. `QUICKSTART.md` - Getting started
2. `README.md` - Full documentation
3. `IMPLEMENTATION_SUMMARY.md` - Technical details

## You're Ready! 🎉

Your LangGraph RAG application is complete and ready to use. Start by running:

```bash
python verify_setup.py
```

Then index some code and start asking questions!

Happy coding! 🚀
