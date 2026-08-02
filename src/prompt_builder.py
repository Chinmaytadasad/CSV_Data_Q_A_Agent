"""Placeholder for prompt construction helpers."""

from __future__ import annotations


def build_code_prompt(schema: str, question: str) -> str:
    raise NotImplementedError


def build_repair_prompt(original_code: str, error: str, question: str) -> str:
    raise NotImplementedError
