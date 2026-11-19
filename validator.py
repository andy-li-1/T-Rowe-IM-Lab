"""Stage 4 — deterministic business-rule checks on the extracted data.

The schema guarantees *shape*; this layer checks *sense*. Each rule returns
human-readable warnings. Add or remove rules as your tax structure changes.
"""

from __future__ import annotations

from typing import Callable, List

from .schema import TaxInput

Rule = Callable[[TaxInput], List[str]]


def rule_tax_year_present(data: TaxInput) -> List[str]:
    return [] if data.taxpayer.tax_year else ["Tax year not identified."]


def rule_filing_status_present(data: TaxInput) -> List[str]:
    return [] if data.taxpayer.filing_status.value else ["Filing status not identified."]


def rule_no_negative_amounts(data: TaxInput) -> List[str]:
    warnings = []
    for item in [*data.income, *data.deductions]:
        if item.amount.value is not None and item.amount.value < 0:
            warnings.append(f"Negative amount for {item.category}: {item.amount.value}")
    return warnings


def rule_amounts_have_quotes(data: TaxInput) -> List[str]:
    return [
        f"{item.category} amount has no supporting quote."
        for item in [*data.income, *data.deductions]
        if item.amount.value is not None and not item.amount.quote
    ]


RULES: List[Rule] = [
    rule_tax_year_present,
    rule_filing_status_present,
    rule_no_negative_amounts,
    rule_amounts_have_quotes,
]


def validate(data: TaxInput) -> List[str]:
    return [w for rule in RULES for w in rule(data)]
