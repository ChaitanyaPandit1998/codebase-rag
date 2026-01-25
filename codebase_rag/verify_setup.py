"""Verify the setup of the codebase RAG application."""
import sys
from pathlib import Path

def verify_setup():
    """Verify that all required components are in place."""
    print("Verifying LangGraph RAG Application Setup...\n")

    issues = []

    # Check .env file
    env_file = Path(".env")
    if not env_file.exists():
        issues.append("❌ .env file not found - copy .env.example to .env and add your API key")
    else:
        print("✓ .env file exists")

        # Check for API key
        with open(env_file) as f:
            content = f.read()
            if "your_openai_api_key_here" in content or not any("OPENAI_API_KEY=" in line and len(line.split("=")[1].strip()) > 10 for line in content.split("\n")):
                issues.append("❌ OPENAI_API_KEY not set in .env file")
            else:
                print("✓ OPENAI_API_KEY appears to be set")

    # Check required directories
    required_dirs = [
        "src/loader",
        "src/processing",
        "src/vectorstore",
        "src/graph",
        "app"
    ]

    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✓ {dir_path}/ exists")
        else:
            issues.append(f"❌ {dir_path}/ not found")

    # Check required files
    required_files = [
        "requirements.txt",
        "src/loader/code_loader.py",
        "src/processing/text_splitter.py",
        "src/vectorstore/chroma_store.py",
        "src/graph/state.py",
        "src/graph/nodes.py",
        "src/graph/workflow.py",
        "app/cli.py"
    ]

    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✓ {file_path} exists")
        else:
            issues.append(f"❌ {file_path} not found")

    # Check if dependencies are installed
    print("\nChecking dependencies...")
    try:
        import langchain
        print("✓ langchain installed")
    except ImportError:
        issues.append("❌ langchain not installed - run: pip install -r requirements.txt")

    try:
        import langgraph
        print("✓ langgraph installed")
    except ImportError:
        issues.append("❌ langgraph not installed - run: pip install -r requirements.txt")

    try:
        import chromadb
        print("✓ chromadb installed")
    except ImportError:
        issues.append("❌ chromadb not installed - run: pip install -r requirements.txt")

    try:
        import openai
        print("✓ openai installed")
    except ImportError:
        issues.append("❌ openai not installed - run: pip install -r requirements.txt")

    # Print summary
    print("\n" + "="*60)
    if issues:
        print("SETUP INCOMPLETE - Please fix the following issues:\n")
        for issue in issues:
            print(issue)
        print("\n" + "="*60)
        return False
    else:
        print("✓ ALL CHECKS PASSED!")
        print("="*60)
        print("\nYou're ready to use the application!")
        print("\nNext steps:")
        print("1. Index a codebase:")
        print("   python -m app.cli index /path/to/your/code")
        print("\n2. Query the codebase:")
        print("   python -m app.cli query 'What does the main function do?'")
        print("\n3. Or use interactive mode:")
        print("   python -m app.cli interactive")
        print()
        return True

if __name__ == "__main__":
    success = verify_setup()
    sys.exit(0 if success else 1)
