"""Main orchestration logic for the CSV data Q&A agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.executor import SecurityError, execute, sanitize
from src.llm_client import generate_code
from src.prompt_builder import build_code_prompt, build_repair_prompt


@dataclass
class AgentResponse:
    question: str
    code: str
    result: Any
    success: bool
    attempts: int
    error_note: str | None = None


def answer_question(df, schema, question) -> AgentResponse:
    """Generate pandas code, execute it, and retry once on failure."""
    prompt = build_code_prompt(schema, question)
    code = generate_code(prompt)

    attempts = 1
    try:
        sanitize(code)
        result = execute(code, df)
        if isinstance(result, str) and result.startswith("UNANSWERABLE"):
            return AgentResponse(
                question=question,
                code=code,
                result=None,
                success=False,
                attempts=attempts,
                error_note=result,
            )

        return AgentResponse(
            question=question,
            code=code,
            result=result,
            success=True,
            attempts=attempts,
        )
    except (SecurityError, Exception) as exc:
        error_note = str(exc)
        repair_prompt = build_repair_prompt(code, error_note, question)
        repaired_code = generate_code(repair_prompt)
        attempts = 2

        try:
            sanitize(repaired_code)
            result = execute(repaired_code, df)
            if isinstance(result, str) and result.startswith("UNANSWERABLE"):
                return AgentResponse(
                    question=question,
                    code=repaired_code,
                    result=None,
                    success=False,
                    attempts=attempts,
                    error_note=result,
                )

            return AgentResponse(
                question=question,
                code=repaired_code,
                result=result,
                success=True,
                attempts=attempts,
            )
        except (SecurityError, Exception) as repair_exc:
            return AgentResponse(
                question=question,
                code=repaired_code,
                result=None,
                success=False,
                attempts=attempts,
                error_note=str(repair_exc),
            )
