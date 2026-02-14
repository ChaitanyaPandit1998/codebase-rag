"""
Codebase RAG CLI

Usage:
  python main.py index <path>               Index a codebase directory
  python main.py explain <logfile>          Explain a log file
  python main.py explain --text "..."       Explain inline log text
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def cmd_index(args: argparse.Namespace) -> None:
    from rag.indexer import index_directory

    root = args.path
    if not Path(root).is_dir():
        print(f"[error] Not a directory: {root}", file=sys.stderr)
        sys.exit(1)

    index_directory(root)


def cmd_explain(args: argparse.Namespace) -> None:
    from rag.retriever import retrieve
    from rag.explainer import explain

    # Get log text
    if args.text:
        log_text = args.text
    elif args.logfile:
        lf = Path(args.logfile)
        if not lf.is_file():
            print(f"[error] Log file not found: {args.logfile}", file=sys.stderr)
            sys.exit(1)
        log_text = lf.read_text(encoding="utf-8", errors="replace")
    else:
        print("[error] Provide a log file path or --text '...'", file=sys.stderr)
        sys.exit(1)

    print("[explain] Retrieving relevant code chunks ...")
    chunks = retrieve(log_text)
    print(f"[explain] Retrieved {len(chunks)} chunks. Calling GPT-4o ...")

    result = explain(log_text, chunks)
    print("\n" + "=" * 60)
    print(result)
    print("=" * 60)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="Codebase RAG: index code and explain logs with Qdrant + GPT-4o",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # index subcommand
    idx = sub.add_parser("index", help="Index a codebase directory into Qdrant")
    idx.add_argument("path", help="Root directory of the codebase to index")

    # explain subcommand
    exp = sub.add_parser("explain", help="Explain a log file using indexed code")
    exp_group = exp.add_mutually_exclusive_group()
    exp_group.add_argument("logfile", nargs="?", help="Path to the log file")
    exp_group.add_argument(
        "--text", "-t", metavar="LOG_TEXT",
        help="Inline log text (use instead of a file path)",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "index":
        cmd_index(args)
    elif args.command == "explain":
        cmd_explain(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
