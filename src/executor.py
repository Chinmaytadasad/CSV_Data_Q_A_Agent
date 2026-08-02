"""Placeholder for code sanitization and execution."""

from __future__ import annotations

import pandas as pd


class SecurityError(Exception):
    pass


def sanitize(code: str) -> str:
    raise NotImplementedError


def execute(code: str, df: pd.DataFrame):
    raise NotImplementedError
