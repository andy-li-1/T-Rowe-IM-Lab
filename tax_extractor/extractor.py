"""Stage 3 — call the LLM and get back a validated `TaxInput`.

Provider-agnostic: uses the OpenAI-compatible chat API (Gemini, Groq, Ollama,
OpenRouter, ...). The schema from schema.py is embedded in the prompt, the
model is asked for JSON, and the reply is validated with Pydantic. If
validation fails, the error is sent back to the model to fix (up to
`max_retries` times).
"""

from __future__ import annotations

import json

from openai import OpenAI
from pydantic import ValidationError

from .config import Settings, load_settings
from .prompts import SYSTEM_PROMPT, build_user_message
from .schema import TaxInput


class ExtractionError(RuntimeError):
    pass


def _schema_instructions() -> str:
    schema = json.dumps(TaxInput.model_json_schema(), indent=2)
    return (
        "Respond with a single JSON object (no prose, no code fences) that "
        f"conforms to this JSON Schema:\n{schema}"
    )


def extract(transcript_text: str, settings: Settings | None = None) -> TaxInput:
    settings = settings or load_settings()
    if not settings.api_key:
        raise ExtractionError(
            f"No API key for provider '{settings.provider}'. See tax_extractor/config.py."
        )
    client = OpenAI(base_url=settings.base_url, api_key=settings.api_key)

    messages = [
        {"role": "system", "content": f"{SYSTEM_PROMPT}\n\n{_schema_instructions()}"},
        {"role": "user", "content": build_user_message(transcript_text)},
    ]

    last_error: Exception | None = None
    for _ in range(settings.max_retries + 1):
        response = client.chat.completions.create(
            model=settings.model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0,
        )
        raw = response.choices[0].message.content or ""
        try:
            return TaxInput.model_validate_json(raw)
        except ValidationError as e:
            last_error = e
            messages += [
                {"role": "assistant", "content": raw},
                {"role": "user", "content": f"That JSON failed validation:\n{e}\nReturn corrected JSON only."},
            ]

    raise ExtractionError(f"Model output never matched the schema: {last_error}")
