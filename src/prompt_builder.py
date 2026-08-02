"""Prompt construction helpers for code generation and repair."""

from __future__ import annotations


SYSTEM_INSTRUCTION = (
    "You are a data analyst. You only output raw pandas code operating on a variable df. "
    "No prose, no explanations, no markdown fences. The last line must assign the answer "
    "to a variable named result. Only output result = 'UNANSWERABLE: <brief reason>' "
    "if the question is gibberish, empty, or has no relation to the dataset's columns or "
    "domain at all. Yes/no questions, existence checks, counting questions, and boolean "
    "questions are answerable and must be handled with real pandas code (for example, "
    ".any(), .empty, len(), or similar) rather than flagged as unanswerable. "    "Do not pre-compute or repeat an expression before assigning it; write the filter or "
    "computation exactly once, directly in the result = ... line. "    "Example: 'are there any sales in Q2?' -> result = not df[df['quarter'] == 'Q2'].empty"
)


def build_code_prompt(schema: str, question: str) -> str:
    """Build the initial prompt for generating pandas code."""
    return (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f"Schema context:\n{schema}\n\n"
        f"Question:\n{question}\n"
    )


def build_repair_prompt(original_code: str, error: str, question: str) -> str:
    """Build a repair prompt after a code execution failure."""
    return (
        f"{SYSTEM_INSTRUCTION}\n\n"
        "The previous attempt failed. Correct it and return only valid pandas code.\n\n"
        f"Original code:\n{original_code}\n\n"
        f"Error:\n{error}\n\n"
        f"Question:\n{question}\n"
    )
