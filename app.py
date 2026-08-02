"""Minimal Streamlit UI for the CSV data Q&A agent."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from src.agent import answer_question
from src.loader import build_schema_context, load_dataset


def _load_uploaded_csv(uploaded_file) -> object:
    suffix = Path(getattr(uploaded_file, "name", "upload.csv")).suffix or ".csv"
    with tempfile.NamedTemporaryFile("wb", suffix=suffix, delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        temp_path = tmp_file.name

    try:
        return load_dataset(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


st.title("CSV / Data Q&A Agent")

if "history" not in st.session_state:
    st.session_state.history = []

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file is not None:
    df = _load_uploaded_csv(uploaded_file)
    schema = build_schema_context(df)

    st.text("Schema detected:")
    st.code(schema)

    with st.form(key="question_form", clear_on_submit=True):
        question = st.text_input("Ask a question about this data")
        submitted = st.form_submit_button("Ask")

    if submitted and question:
        response = answer_question(df, schema, question)
        st.session_state.history.append(response)

        for response in reversed(st.session_state.history):
            st.subheader(f"Q: {response.question}")
            if isinstance(response.result, pd.DataFrame):
                display_df = response.result.copy()
                for column in display_df.columns:
                    if display_df[column].dtype == "object":
                        display_df[column] = display_df[column].astype(str)
                st.dataframe(display_df)
            elif isinstance(response.result, pd.Series):
                st.dataframe(response.result.to_frame(name="value"))
            else:
                st.write(response.result)
            st.subheader("Code used")
            st.code(response.code, language="python")
            if not response.success:
                st.error(response.error_note)
            st.divider()
