"""Stage 1 — load and normalize a raw transcript."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Transcript:
    source: str  # file path or identifier
    text: str    # cleaned transcript text


def load_transcript(path: str | Path) -> Transcript:
    """Read a transcript file. Extend here for .vtt/.srt/.json formats."""
    path = Path(path)
    raw = path.read_text(encoding="utf-8")
    return Transcript(source=str(path), text=clean(raw))


def clean(text: str) -> str:
    """Light normalization. Add PII redaction / speaker relabeling here if needed."""
    text = text.replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
