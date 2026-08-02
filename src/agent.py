"""Placeholder for the main agent orchestration logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AgentResponse:
    question: str
    code: str
    result: Any
    success: bool
    attempts: int
    error_note: str | None = None


def answer_question(df, schema, question) -> AgentResponse:
    raise NotImplementedError
