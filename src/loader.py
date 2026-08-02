"""Placeholder for dataset loading and schema context utilities."""

from __future__ import annotations

import pandas as pd


def load_dataset(path: str) -> pd.DataFrame:
    raise NotImplementedError


def build_schema_context(df: pd.DataFrame) -> str:
    raise NotImplementedError
