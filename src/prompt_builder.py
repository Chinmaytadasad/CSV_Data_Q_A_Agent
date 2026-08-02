"""Prompt construction helpers for code generation and repair."""

from __future__ import annotations


SYSTEM_INSTRUCTION = (
    "You are a data analyst. You only output raw pandas code operating on a variable df. "
    "No prose, no explanations, no markdown fences. The last line must assign the answer "
    "to a variable named result. If the question is not a coherent, answerable question "
    "about the dataset, output only result = 'UNANSWERABLE: <brief reason>'."
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
