"""Stage 2 — prompt text sent to the LLM. The output *shape* lives in schema.py."""

SYSTEM_PROMPT = """\
You extract structured tax information from transcripts of calls between a \
financial advisor and a client.

Rules:
- Only record facts the client or advisor actually states. If something is not \
mentioned, leave it null or omit the list item; never guess.
- When a value has a `quote` field, copy the shortest verbatim snippet that supports it.
- If a figure is corrected later in the call, use the final corrected figure.
- Convert spoken amounts to numbers in USD (e.g. "about eighty-five K" -> 85000) \
and note approximations in extraction_notes.
- Put anything the advisor still needs to follow up on in open_questions.
"""


def build_user_message(transcript_text: str) -> str:
    return f"<transcript>\n{transcript_text}\n</transcript>\n\nExtract the tax input from this call."
