"""
Build a GPT-4o prompt from the log + retrieved code chunks, return an explanation.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI

from rag.config import CHAT_MODEL, CHAT_TEMPERATURE

load_dotenv()

_SYSTEM_PROMPT = """\
You are an expert software engineer analyzing application logs.
You will be given:
1. A log excerpt (possibly containing errors, stack traces, or execution output).
2. Relevant source code chunks retrieved from the codebase.

Your task:
- Trace the execution flow step by step, referencing specific file names and line numbers from the chunk headers — never refer to chunks by number.
- Explain what each relevant function or method does in the context of the log.
- Explain any calculations, transformations, or business logic involved.
- When the log output contains concrete runtime values (arguments, return values, thresholds),
  cross-reference them with the source code and call out what was passed — e.g.
  "OrderProcessor was initialised with discount_rate=0.10".
- Identify the root cause of any errors or unexpected behavior.
- Be concise but thorough. Use bullet points and section headers for clarity.
"""


def _openai_client() -> OpenAI:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. Add it to .env or export it."
        )
    return OpenAI(api_key=key)


def _build_user_prompt(log_text: str, chunks: list[dict]) -> str:
    sections = ["## Log Content\n```\n" + log_text.strip() + "\n```\n"]

    sections.append("## Retrieved Code Chunks\n")
    for item in chunks:
        p = item["payload"]
        header = (
            f"### {p.get('file_path', 'unknown')}"
            f"  (lines {p.get('line_start', '?')}–{p.get('line_end', '?')})"
            f"  [{p.get('language', '?')} / {p.get('chunk_type', '?')}]"
        )
        if p.get("class_name"):
            header += f"  class: {p['class_name']}"
        if p.get("function_name"):
            header += f"  function: {p['function_name']}"
        source = p.get("source", "").strip()
        sections.append(f"{header}\n```{p.get('language', '')}\n{source}\n```\n")

    return "\n".join(sections)


def explain(log_text: str, chunks: list[dict]) -> str:
    """Call GPT-4o to explain the log given retrieved code chunks."""
    if not chunks:
        return (
            "No relevant code chunks were retrieved from the index. "
            "Make sure the codebase has been indexed first with `python main.py index <path>`."
        )

    client = _openai_client()
    user_prompt = _build_user_prompt(log_text, chunks)

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=CHAT_TEMPERATURE,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""
