"""Dataset loading and schema context utilities."""

from __future__ import annotations

import pandas as pd


def _describe_object_column(series: pd.Series) -> str:
    """Describe object-dtype values in a compact, LLM-friendly way."""
    non_null_values = [value for value in series.dropna().tolist() if value is not None]

    if not non_null_values:
        return "object (all null)"

    if all(isinstance(value, bool) for value in non_null_values):
        return "object (boolean values: True/False, use == True/False, not string comparison)"

    if all(isinstance(value, str) for value in non_null_values):
        return "object (string values)"

    type_names = sorted({type(value).__name__ for value in non_null_values})
    return f"object (mixed types: {', '.join(type_names)})"


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
    dtype_labels = {}
    for name, dtype in df.dtypes.items():
        if dtype == "object":
            dtype_labels[name] = _describe_object_column(df[name])
        else:
            dtype_labels[name] = str(dtype)
    non_null_counts = df.notna().sum().to_dict()

    sample_rows = df.head(3).to_string(index=False)

    lines = [
        f"Columns: {', '.join(columns)}",
        "Data types:",
    ]
    lines.extend(f"- {name}: {dtype_labels[name]}" for name in columns)
    lines.append("Non-null counts:")
    lines.extend(f"- {name}: {count}" for name, count in non_null_counts.items())
    lines.append("Sample rows:")
    lines.append(sample_rows)

    return "\n".join(lines)
