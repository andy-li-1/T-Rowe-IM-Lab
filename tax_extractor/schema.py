"""
THE TAX STRUCTURE — edit this file to change what gets extracted.

Everything downstream (the LLM's output format, validation, JSON output) is
driven by `TaxInput`. Add, remove, or rename fields here; the field names and
`description=` strings are sent to the model as the schema, so write
descriptions as instructions ("Annual W-2 wages in USD").

Conventions used below (keep them or change them consistently):
  - Every field is Optional: if the call never mentions it, the model returns null
    rather than guessing.
  - Money is a float in USD.
  - `Sourced[...]` wraps values where you want the transcript quote that justifies them.
"""

from __future__ import annotations

from typing import Generic, List, Literal, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# --------------------------------------------------------------------------- #
# Building blocks
# --------------------------------------------------------------------------- #
class Sourced(BaseModel, Generic[T]):
    """A value plus the transcript evidence for it (for auditability)."""

    value: Optional[T] = Field(None, description="The extracted value, or null if not stated.")
    quote: Optional[str] = Field(None, description="Verbatim transcript snippet supporting the value.")


FilingStatus = Literal[
    "single",
    "married_filing_jointly",
    "married_filing_separately",
    "head_of_household",
    "qualifying_surviving_spouse",
]


# --------------------------------------------------------------------------- #
# Sections — PLACEHOLDERS, replace with your real structure
# --------------------------------------------------------------------------- #
class Taxpayer(BaseModel):
    full_name: Optional[str] = None
    tax_year: Optional[int] = Field(None, description="Tax year being discussed, e.g. 2025.")
    filing_status: Sourced[FilingStatus] = Field(default_factory=Sourced)
    state_of_residence: Optional[str] = Field(None, description="Two-letter US state code.")


class Dependent(BaseModel):
    name: Optional[str] = None
    relationship: Optional[str] = None
    age: Optional[int] = None


class IncomeItem(BaseModel):
    category: Literal["w2_wages", "self_employment", "interest", "dividends", "capital_gains", "rental", "other"]
    description: Optional[str] = None
    amount: Sourced[float] = Field(default_factory=Sourced)


class DeductionItem(BaseModel):
    category: Literal["mortgage_interest", "charitable", "state_local_taxes", "medical", "retirement_contribution", "other"]
    description: Optional[str] = None
    amount: Sourced[float] = Field(default_factory=Sourced)


# --------------------------------------------------------------------------- #
# Top-level object the LLM must return
# --------------------------------------------------------------------------- #
class TaxInput(BaseModel):
    """Structured tax input extracted from one call transcript."""

    taxpayer: Taxpayer = Field(default_factory=Taxpayer)
    dependents: List[Dependent] = Field(default_factory=list)
    income: List[IncomeItem] = Field(default_factory=list)
    deductions: List[DeductionItem] = Field(default_factory=list)

    # Meta fields — useful regardless of what tax structure you settle on.
    open_questions: List[str] = Field(
        default_factory=list,
        description="Information the advisor still needs that was not resolved on the call.",
    )
    extraction_notes: Optional[str] = Field(
        None, description="Ambiguities or assumptions the model made."
    )
