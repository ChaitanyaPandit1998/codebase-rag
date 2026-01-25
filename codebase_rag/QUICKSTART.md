# Quick Start Guide

Get up and running with the LangGraph RAG application in 5 minutes.

## Step 1: Install Dependencies

```bash
cd codebase_rag
pip install -r requirements.txt
```

## Step 2: Configure API Key

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your OpenAI API key:
```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
```

Get your API key from: https://platform.openai.com/api-keys

## Step 3: Verify Setup

```bash
python verify_setup.py
```

This will check that all files are in place and dependencies are installed.

## Step 4: Index a Codebase

Let's index the application itself as a test:

```bash
python -m app.cli index ./src
```

You should see output like:
```
============================================================
INDEXING CODEBASE: ./src
============================================================

Loading code files...
Loaded 7 files:
  .py: 7 files
Total characters: 15,234

Splitting documents into chunks...
Created 45 chunks

Creating vector store...
Vector store created at ./chroma_db

============================================================
INDEXING COMPLETE
============================================================
```

## Step 5: Query Your Codebase

Now try asking questions:

```bash
python -m app.cli query "What is the GraphState used for?"
```

Or start an interactive session:

```bash
python -m app.cli interactive
```

## Example Queries

Try these questions about the indexed codebase:

- `"How does the code loader work?"`
- `"What nodes are in the LangGraph workflow?"`
- `"Explain the document grading process"`
- `"How are documents split into chunks?"`
- `"What does the ChromaStore class do?"`

## Troubleshooting

### Import Errors
If you see import errors, make sure you're in the `codebase_rag` directory and have installed all dependencies:
```bash
pip install -r requirements.txt
```

### API Key Issues
If you get authentication errors:
1. Check that your `.env` file exists
2. Verify your API key is correct (starts with `sk-`)
3. Make sure there are no extra spaces or quotes around the key

### No Documents Found
If indexing finds no documents:
- Check that the path is correct
- Make sure there are `.py` files in the directory
- Try specifying the full absolute path

## Next Steps

- Index your own project: `python -m app.cli index /path/to/your/project`
- Customize settings in `.env` file
- Read the full README.md for advanced usage
- Try different file extensions: `--extensions .py .js .ts`

## Need Help?

Check the README.md for detailed documentation and troubleshooting.
