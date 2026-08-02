"""Code sanitization and restricted execution for generated pandas snippets."""

from __future__ import annotations

import ast

import pandas as pd


class SecurityError(Exception):
    pass


def sanitize(code: str) -> str:
    """Reject code that uses forbidden constructs."""
    if not isinstance(code, str):
        raise TypeError("Code must be provided as a string")

    forbidden_tokens = [
        "import",
        "exec",
        "eval",
        "__",
        "open(",
        "os.",
        "sys.",
        "subprocess",
    ]

    lowered = code.lower()
    for token in forbidden_tokens:
        if token in lowered:
            raise SecurityError(f"Unsafe code detected: contains {token}")

    return code


def execute(code: str, df: pd.DataFrame):
    """Execute sanitized code in a restricted namespace and return the result."""
    sanitized_code = sanitize(code)
    try:
        ast.parse(sanitized_code)
    except SyntaxError as exc:
        raise SyntaxError(f"Invalid Python syntax: {exc.msg}") from exc

    namespace = {"pd": pd, "df": df.copy(), "__builtins__": {}}

    try:
        exec(sanitized_code, namespace, namespace)
    except Exception:
        raise

    if "result" not in namespace:
        raise ValueError("Executed code did not define a result variable")

    return namespace["result"]
