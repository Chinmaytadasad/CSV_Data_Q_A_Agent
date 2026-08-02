from __future__ import annotations

import os
import re
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def _strip_code_fences(text: str) -> str:
    if not text:
        return ""

    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:[A-Za-z0-9_-]+)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
    return cleaned.strip()


def _extract_text(response: Any) -> str:
    if hasattr(response, "choices") and getattr(response, "choices", None):
        message = response.choices[0].message
        content = getattr(message, "content", "")
        if isinstance(content, list):
            return "".join(
                str(getattr(item, "text", "") or "") for item in content
            )
        return str(content or "")

    if hasattr(response, "content"):
        content = response.content
        if isinstance(content, list):
            return "".join(
                str(getattr(item, "text", "") or "") for item in content
            )
        return str(content or "")

    return str(response or "")


def generate_code(prompt: str) -> str:
    """Generate raw pandas code from the supplied prompt."""
    if not prompt or not prompt.strip():
        raise ValueError("Prompt must not be empty")

    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise RuntimeError("No API key found. Set GROQ_API_KEY in your environment.")

    try:
        from groq import Groq
    except ImportError as exc:  # pragma: no cover - runtime dependency guard
        raise RuntimeError("The 'groq' package is required.") from exc

    client = Groq(api_key=groq_api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1000,
    )
    return _strip_code_fences(_extract_text(response))
