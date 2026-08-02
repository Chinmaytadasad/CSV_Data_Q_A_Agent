"""Interactive CLI for the CSV data Q&A agent."""

from __future__ import annotations

import argparse

import pandas as pd

from src.agent import answer_question
from src.loader import build_schema_context, load_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask questions about a CSV dataset")
    parser.add_argument("dataset", nargs="?", default="data/sample_sales.csv")
    args = parser.parse_args()

    df = load_dataset(args.dataset)
    schema = build_schema_context(df)

    print("Loaded dataset:")
    print(schema)
    print("\nType 'exit' or 'quit' to leave the session.\n")

    while True:
        question = input("Ask a question: ").strip()
        if question.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        if not question:
            continue

        response = answer_question(df, schema, question)
        print("\nCode used:")
        print(response.code)
        if not response.success:
            print(f"\nAttempts: {response.attempts}")
            print(f"Error: {response.error_note}")
            continue

        print("\nResult:")
        if isinstance(response.result, pd.DataFrame):
            print(response.result.to_string(index=False))
        else:
            print(response.result)


if __name__ == "__main__":
    main()
