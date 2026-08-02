"""Code sanitization and restricted execution for generated pandas snippets."""

from __future__ import annotations

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
    restricted_globals = {"pd": pd, "__builtins__": {} }
    restricted_locals = {"df": df.copy()}

    try:
        exec(sanitized_code, restricted_globals, restricted_locals)
    except Exception:
        raise

    if "result" not in restricted_locals:
        raise NameError("Executed code did not define a result variable")

    return restricted_locals["result"]
