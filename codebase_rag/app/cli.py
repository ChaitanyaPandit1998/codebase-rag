"""Command-line interface for the codebase RAG application."""
import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.loader import CodeLoader
from src.processing import get_code_splitter
from src.vectorstore import ChromaStore
from src.graph import create_workflow


def index_command(args):
    """Index a codebase."""
    print(f"\n{'='*60}")
    print(f"INDEXING CODEBASE: {args.path}")
    print(f"{'='*60}\n")

    # Load documents
    print("Loading code files...")
    loader = CodeLoader(args.path, file_extensions=args.extensions or ['.py'])
    documents = loader.load_documents()

    if not documents:
        print("No documents found to index!")
        return

    # Print stats
    stats = loader.get_stats(documents)
    print(f"\nLoaded {stats['total_files']} files:")
    for ext, count in stats['files_by_extension'].items():
        print(f"  {ext}: {count} files")
    print(f"Total characters: {stats['total_characters']:,}")

    # Split documents
    print("\nSplitting documents into chunks...")
    splitter = get_code_splitter(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )
    split_docs = splitter.split_documents(documents)
    print(f"Created {len(split_docs)} chunks")

    # Create vector store
    print("\nCreating vector store...")
    store = ChromaStore(
        persist_directory=args.db_path,
        collection_name=args.collection
    )

    # Delete existing collection if it exists
    try:
        store.delete_collection()
    except:
        pass

    store.create(split_docs)

    # Print final stats
    store_stats = store.get_stats()
    print(f"\n{'='*60}")
    print(f"INDEXING COMPLETE")
    print(f"{'='*60}")
    print(f"Collection: {store_stats['collection_name']}")
    print(f"Documents indexed: {store_stats['document_count']}")
    print(f"Location: {store_stats['persist_directory']}")
    print()


def query_command(args):
    """Query the codebase."""
    print(f"\n{'='*60}")
    print(f"QUERY: {args.question}")
    print(f"{'='*60}\n")

    # Load vector store
    store = ChromaStore(
        persist_directory=args.db_path,
        collection_name=args.collection
    )

    try:
        retriever = store.as_retriever()
    except ValueError as e:
        print(f"Error: {e}")
        return

    # Create and run workflow
    print("Processing query through LangGraph workflow...\n")
    workflow = create_workflow(retriever)

    # Run the workflow
    result = workflow.invoke({
        "question": args.question,
        "documents": [],
        "generation": "",
        "relevance_score": "",
        "retry_count": 0
    })

    # Print result
    print(f"\n{'='*60}")
    print(f"ANSWER")
    print(f"{'='*60}\n")
    print(result['generation'])
    print(f"\n{'='*60}")
    print(f"Retrieved {len(result['documents'])} relevant documents")
    print(f"{'='*60}\n")


def interactive_command(args):
    """Interactive query mode."""
    print(f"\n{'='*60}")
    print(f"INTERACTIVE MODE")
    print(f"{'='*60}")
    print("Type 'exit' or 'quit' to end the session")
    print(f"{'='*60}\n")

    # Load vector store
    store = ChromaStore(
        persist_directory=args.db_path,
        collection_name=args.collection
    )

    try:
        retriever = store.as_retriever()
        store_stats = store.get_stats()
        print(f"Loaded collection: {store_stats['collection_name']}")
        print(f"Documents available: {store_stats['document_count']}\n")
    except ValueError as e:
        print(f"Error: {e}")
        return

    # Create workflow
    workflow = create_workflow(retriever)

    # Interactive loop
    while True:
        try:
            question = input("\nQuestion: ").strip()

            if question.lower() in ['exit', 'quit', 'q']:
                print("\nGoodbye!")
                break

            if not question:
                continue

            print(f"\n{'-'*60}")
            print("Processing...")
            print(f"{'-'*60}\n")

            # Run workflow
            result = workflow.invoke({
                "question": question,
                "documents": [],
                "generation": "",
                "relevance_score": "",
                "retry_count": 0
            })

            # Print result
            print(f"\n{'='*60}")
            print("ANSWER")
            print(f"{'='*60}\n")
            print(result['generation'])
            print(f"\n{'-'*60}")
            print(f"Retrieved {len(result['documents'])} relevant documents")
            print(f"{'-'*60}")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


def main():
    """Main CLI entry point."""
    # Load environment variables
    load_dotenv()

    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY not found in environment variables")
        print("Please create a .env file with your OpenAI API key")
        sys.exit(1)

    # Create main parser
    parser = argparse.ArgumentParser(
        description='LangGraph RAG application for codebase querying'
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Index command
    index_parser = subparsers.add_parser('index', help='Index a codebase')
    index_parser.add_argument(
        'path',
        help='Path to the codebase directory'
    )
    index_parser.add_argument(
        '--extensions',
        nargs='+',
        default=['.py'],
        help='File extensions to index (default: .py)'
    )
    index_parser.add_argument(
        '--chunk-size',
        type=int,
        default=None,
        help='Chunk size for text splitting'
    )
    index_parser.add_argument(
        '--chunk-overlap',
        type=int,
        default=None,
        help='Chunk overlap for text splitting'
    )
    index_parser.add_argument(
        '--db-path',
        default=None,
        help='Path to ChromaDB database'
    )
    index_parser.add_argument(
        '--collection',
        default='codebase',
        help='Collection name'
    )

    # Query command
    query_parser = subparsers.add_parser('query', help='Query the codebase')
    query_parser.add_argument(
        'question',
        help='Question to ask about the codebase'
    )
    query_parser.add_argument(
        '--db-path',
        default=None,
        help='Path to ChromaDB database'
    )
    query_parser.add_argument(
        '--collection',
        default='codebase',
        help='Collection name'
    )

    # Interactive command
    interactive_parser = subparsers.add_parser(
        'interactive',
        help='Interactive query mode'
    )
    interactive_parser.add_argument(
        '--db-path',
        default=None,
        help='Path to ChromaDB database'
    )
    interactive_parser.add_argument(
        '--collection',
        default='codebase',
        help='Collection name'
    )

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == 'index':
        index_command(args)
    elif args.command == 'query':
        query_command(args)
    elif args.command == 'interactive':
        interactive_command(args)


if __name__ == '__main__':
    main()
