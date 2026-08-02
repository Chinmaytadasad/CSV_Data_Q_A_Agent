"""Dataset loading and schema context utilities."""

from __future__ import annotations

import pandas as pd


def load_dataset(path: str) -> pd.DataFrame:
    """Load a CSV or Excel file into a pandas DataFrame."""
    if path.endswith(".csv"):
        return pd.read_csv(path)
    if path.endswith((".xlsx", ".xls")):
        return pd.read_excel(path)
    raise ValueError("Unsupported file type. Use a .csv or .xlsx/.xls file.")


def build_schema_context(df: pd.DataFrame) -> str:
    """Return a compact schema summary suitable for LLM prompts."""
    columns = list(df.columns)
    dtypes = df.dtypes.astype(str).to_dict()
    non_null_counts = df.notna().sum().to_dict()

    sample_rows = df.head(3).to_string(index=False)

    lines = [
        f"Columns: {', '.join(columns)}",
        "Data types:",
    ]
    lines.extend(f"- {name}: {dtype}" for name, dtype in dtypes.items())
    lines.append("Non-null counts:")
    lines.extend(f"- {name}: {count}" for name, count in non_null_counts.items())
    lines.append("Sample rows:")
    lines.append(sample_rows)

    return "\n".join(lines)
