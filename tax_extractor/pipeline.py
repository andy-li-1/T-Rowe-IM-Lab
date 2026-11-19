"""Orchestration: load -> extract -> validate -> write."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from .config import Settings
from .extractor import extract
from .loader import clean, load_transcript
from .schema import TaxInput
from .validator import validate


@dataclass
class PipelineResult:
    source: str
    data: TaxInput
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"source": self.source, "warnings": self.warnings, "tax_input": self.data.model_dump()}


def run(transcript_path: str | Path, settings: Settings | None = None) -> PipelineResult:
    transcript = load_transcript(transcript_path)
    return run_text(transcript.text, source=transcript.source, settings=settings)


def run_text(text: str, source: str = "transcript", settings: Settings | None = None) -> PipelineResult:
    """Same pipeline, starting from raw text (used by the web UI)."""
    data = extract(clean(text), settings)
    return PipelineResult(source=source, data=data, warnings=validate(data))


def write_result(result: PipelineResult, out_dir: str | Path = "output") -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{Path(result.source).stem}.json"
    out_path.write_text(json.dumps(result.to_dict(), indent=2))
    return out_path
