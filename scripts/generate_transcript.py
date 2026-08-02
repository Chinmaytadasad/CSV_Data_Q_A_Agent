from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agent import answer_question
from src.loader import build_schema_context, load_dataset


DATASET_PATH = ROOT / "data" / "sample_sales.csv"
OUTPUT_PATH = ROOT / "sample_qa" / "qa_transcript.md"


def format_result(result: object) -> str:
    if isinstance(result, (pd.DataFrame, pd.Series)):
        return result.to_string()
    if result is None:
        return "None"
    return str(result)


def build_questions() -> list[str]:
    return [
        "What is the total revenue for the East region?",
        "Which product has the highest average revenue by region?",
        "Are there any sales in Q2?",
        "What is the average units_sold for the North region where revenue is greater than 5000?",
        "What are the top 3 products by revenue?",
        "List all rows where the region is West and units_sold is greater than 100.",
        "What are the sales trends for the mysterious region and product?",
        "What is the total revenue for the East region in Q2 and the average units_sold for Alpha products?",
        "What is the revenue for the nonexistent entity Zeta?",
        "What is the total revnue for the North region?",
    ]


def main() -> None:
    df = load_dataset(str(DATASET_PATH))
    schema = build_schema_context(df)
    questions = build_questions()

    sections: list[str] = []
    for question in questions:
        try:
            response = answer_question(df, schema, question)
        except Exception as exc:  # pragma: no cover - defensive logging for transcript generation
            response = None
            error_text = str(exc)

        if response is None:
            code_text = ""
            result_text = f"ERROR: {error_text}"
        else:
            code_text = response.code or ""
            if response.success:
                result_text = format_result(response.result)
            else:
                result_text = f"Failed — {response.error_note or 'unknown error'}"

        section = (
            f"### Q: {question}\n\n"
            f"**Code used:**\n"
            f"```python\n{code_text}\n```\n\n"
            f"**Result:**\n"
            f"{result_text}\n\n"
            f"---\n\n"
        )
        sections.append(section)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("".join(sections), encoding="utf-8")
    print(f"Wrote transcript to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
