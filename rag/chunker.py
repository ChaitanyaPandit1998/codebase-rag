"""
Parse Python and Java source files into code chunks.

Each chunk is a dict with keys:
  file_path, file_name, language, chunk_type, function_name, class_name,
  package, line_start, line_end, source
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Iterator


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------

def _make_chunk(
    file_path: str,
    language: str,
    chunk_type: str,
    line_start: int,
    line_end: int,
    source: str,
    function_name: str = "",
    class_name: str = "",
    package: str = "",
) -> dict:
    return {
        "file_path": file_path,
        "file_name": Path(file_path).name,
        "language": language,
        "chunk_type": chunk_type,
        "function_name": function_name,
        "class_name": class_name,
        "package": package,
        "line_start": line_start,
        "line_end": line_end,
        "source": source,
    }


def _lines_to_source(lines: list[str], start: int, end: int) -> str:
    """Return source text for lines[start-1 : end] (1-indexed, inclusive)."""
    return "".join(lines[start - 1 : end])


# ---------------------------------------------------------------------------
# Python chunker
# ---------------------------------------------------------------------------

def _python_module_path(file_path: str) -> str:
    """Convert file path to dot-separated module path."""
    p = Path(file_path)
    parts = list(p.with_suffix("").parts)
    return ".".join(parts)


def chunk_python(file_path: str) -> list[dict]:
    """Parse a .py file and return a list of chunks."""
    text = Path(file_path).read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=True)
    package = _python_module_path(file_path)
    chunks: list[dict] = []

    try:
        tree = ast.parse(text, filename=file_path)
    except SyntaxError:
        # Fallback: whole file as one chunk
        return [
            _make_chunk(
                file_path, "python", "module_level",
                1, len(lines), text,
                package=package,
            )
        ]

    # Track top-level and class-level nodes
    visited_lines: set[int] = set()

    def get_source(node: ast.AST) -> str:
        try:
            src = ast.get_source_segment(text, node)
            if src:
                return src
        except Exception:
            pass
        # Fallback to line slicing
        start = node.lineno  # type: ignore[attr-defined]
        end = node.end_lineno  # type: ignore[attr-defined]
        return _lines_to_source(lines, start, end)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Class-level chunk (full class body)
            cls_src = get_source(node)
            chunks.append(
                _make_chunk(
                    file_path, "python", "class",
                    node.lineno, node.end_lineno, cls_src,
                    class_name=node.name,
                    package=package,
                )
            )
            for line in range(node.lineno, node.end_lineno + 1):
                visited_lines.add(line)

            # Individual methods
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_src = get_source(item)
                    chunks.append(
                        _make_chunk(
                            file_path, "python", "method",
                            item.lineno, item.end_lineno, method_src,
                            function_name=item.name,
                            class_name=node.name,
                            package=package,
                        )
                    )

        elif isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef)
        ) and isinstance(getattr(node, "parent", None), type(None)):
            # Only top-level functions (not inside classes)
            # We need to check parent; ast.walk doesn't track parents
            pass  # handled below

    # Second pass: top-level functions only
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fn_src = get_source(node)
            chunks.append(
                _make_chunk(
                    file_path, "python", "function",
                    node.lineno, node.end_lineno, fn_src,
                    function_name=node.name,
                    package=package,
                )
            )
            for line in range(node.lineno, node.end_lineno + 1):
                visited_lines.add(line)

    # Module-level code: lines not covered by any class or function
    module_lines = [
        line for i, line in enumerate(lines, start=1)
        if i not in visited_lines
    ]
    # Filter blank-only content
    non_blank = [l for l in module_lines if l.strip()]
    if len(non_blank) > 3:
        # Reconstruct a contiguous source block (with line numbers for readability)
        module_src = "".join(module_lines)
        # Find actual line range
        covered_module = [
            i for i in range(1, len(lines) + 1)
            if i not in visited_lines and lines[i - 1].strip()
        ]
        if covered_module:
            chunks.append(
                _make_chunk(
                    file_path, "python", "module_level",
                    covered_module[0], covered_module[-1], module_src,
                    package=package,
                )
            )

    return chunks


# ---------------------------------------------------------------------------
# Java chunker
# ---------------------------------------------------------------------------

def _find_end_line_brace(lines: list[str], start_line: int) -> int:
    """
    Starting from start_line (1-indexed), scan for the closing brace that
    balances the opening brace of a class or method.
    Returns the 1-indexed line of the closing brace, or len(lines).
    """
    depth = 0
    found_open = False
    for i in range(start_line - 1, len(lines)):
        for ch in lines[i]:
            if ch == "{":
                depth += 1
                found_open = True
            elif ch == "}":
                depth -= 1
                if found_open and depth == 0:
                    return i + 1  # 1-indexed
    return len(lines)


def _java_package(tree) -> str:  # type: ignore[return]
    """Extract package name from a javalang CompilationUnit."""
    try:
        if tree.package:
            return tree.package.name
    except Exception:
        pass
    return ""


def chunk_java(file_path: str) -> list[dict]:
    """Parse a .java file and return a list of chunks."""
    try:
        import javalang  # type: ignore
    except ImportError:
        raise ImportError("javalang is required: uv add javalang")

    text = Path(file_path).read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=True)
    chunks: list[dict] = []

    try:
        tree = javalang.parse.parse(text)
    except Exception:
        # Fallback: whole file as one chunk
        return [
            _make_chunk(
                file_path, "java", "module_level",
                1, len(lines), text,
            )
        ]

    package = _java_package(tree)

    for _, type_decl in tree.filter(javalang.tree.TypeDeclaration):
        if not hasattr(type_decl, "name"):
            continue
        cls_name = type_decl.name
        cls_line = type_decl.position.line if type_decl.position else 1
        cls_end = _find_end_line_brace(lines, cls_line)
        cls_src = _lines_to_source(lines, cls_line, cls_end)

        chunk_type = (
            "class"
            if isinstance(type_decl, javalang.tree.ClassDeclaration)
            else "class"  # InterfaceDeclaration also maps to class
        )

        chunks.append(
            _make_chunk(
                file_path, "java", chunk_type,
                cls_line, cls_end, cls_src,
                class_name=cls_name,
                package=package,
            )
        )

        # Methods and constructors
        for member in (type_decl.body or []):
            if not isinstance(
                member,
                (javalang.tree.MethodDeclaration, javalang.tree.ConstructorDeclaration),
            ):
                continue
            if not member.position:
                continue
            method_name = member.name
            method_line = member.position.line
            method_end = _find_end_line_brace(lines, method_line)
            method_src = _lines_to_source(lines, method_line, method_end)
            chunks.append(
                _make_chunk(
                    file_path, "java", "method",
                    method_line, method_end, method_src,
                    function_name=method_name,
                    class_name=cls_name,
                    package=package,
                )
            )

    return chunks


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def chunk_file(file_path: str) -> list[dict]:
    """Dispatch to the appropriate chunker based on file extension."""
    ext = Path(file_path).suffix.lower()
    if ext == ".py":
        return chunk_python(file_path)
    elif ext == ".java":
        return chunk_java(file_path)
    return []
