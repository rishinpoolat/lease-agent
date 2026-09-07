"""R1-R7 rule engine — see docs/context/03-validation-rules.md.

Rule text/severity/check descriptions are never duplicated here — they live
in docs/owner_ruleset.json, read live by load_ruleset(). This module only
implements the check *logic*, mapped by rule_id.
"""

import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from agents.paths import resolve_path
from agents.schemas import ExtractedField

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_RULESET_PATH = resolve_path("RULESET_JSON_PATH", REPO_ROOT / "docs" / "owner_ruleset.json")

Verdict = Literal["PASS", "FAIL", "NOT_DETERMINABLE"]


class RuleResult(BaseModel):
    rule_id: str
    verdict: Verdict
    reason: str
    source_field_refs: list[str]


class UnitRecord(BaseModel):
    unit_id: str
    label: str
    status: str


def load_ruleset(path: Path = DEFAULT_RULESET_PATH) -> dict:
    return json.loads(path.read_text())


def _field(fields: dict[str, ExtractedField], name: str) -> ExtractedField | None:
    f = fields.get(name)
    if f is None or f.confidence == "not_found":
        return None
    return f


def _months_between(start: date, end: date) -> int:
    """Calendar months between two dates, day-aware (11 months + 28 days
    rounds down to 11, not 12) — deliberately strict, since R4 checking
    "stated term matches dates" is exactly meant to catch a lease that
    phrases an inclusive-end-date term loosely (e.g. "12 months" from
    Mar 1 to the following Feb 28)."""
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day < start.day:
        months -= 1
    return months


def _not_determinable(rule_id: str, reason: str, refs: list[str]) -> RuleResult:
    return RuleResult(rule_id=rule_id, verdict="NOT_DETERMINABLE", reason=reason, source_field_refs=refs)


def _money(field: ExtractedField) -> Decimal | None:
    """Money fields are stored as exact decimal strings (see stub.py's
    `_money`), never float -- JSON has no native decimal type, and a float
    round-trip is exactly the kind of silent precision loss that shouldn't
    touch a rent/deposit comparison. Returns None if the value isn't a
    parseable decimal (defensive; the stub never produces one that isn't)."""
    try:
        return Decimal(str(field.value))
    except (InvalidOperation, TypeError):
        return None


def _normalize_monthly_rent(fields: dict[str, ExtractedField]) -> tuple[Decimal, list[str]] | None:
    rent = _field(fields, "rent_amount")
    freq = _field(fields, "rent_frequency")
    if rent is None or freq is None:
        return None
    rent_decimal = _money(rent)
    if rent_decimal is None:
        return None
    refs = ["rent_amount", "rent_frequency"]
    if freq.value == "monthly":
        return rent_decimal, refs
    if freq.value == "annual":
        return rent_decimal / 12, refs
    return None


def check_r1(fields: dict[str, ExtractedField], units: dict[str, UnitRecord]) -> RuleResult:
    deposit = _field(fields, "deposit_amount")
    monthly = _normalize_monthly_rent(fields)
    deposit_decimal = _money(deposit) if deposit is not None else None
    if deposit_decimal is None or monthly is None:
        return _not_determinable(
            "R1", "deposit_amount or rent (amount/frequency) missing or unreadable",
            ["deposit_amount", "rent_amount", "rent_frequency"],
        )
    monthly_rent, rent_refs = monthly
    refs = ["deposit_amount", *rent_refs]
    if deposit_decimal >= monthly_rent:
        return RuleResult(rule_id="R1", verdict="PASS", reason="Deposit covers at least one month's rent", source_field_refs=refs)
    return RuleResult(
        rule_id="R1", verdict="FAIL",
        reason=f"Deposit {deposit.value} is less than one month's rent ({monthly_rent})",
        source_field_refs=refs,
    )


def check_r2(fields: dict[str, ExtractedField], units: dict[str, UnitRecord]) -> RuleResult:
    clause = _field(fields, "escalation_clause")
    if clause is None:
        return _not_determinable("R2", "Escalation clause text missing or unreadable", ["escalation_clause"])
    value = clause.value
    if isinstance(value, dict):
        is_defined = value.get("is_defined")
        text = str(value.get("mechanism_text", "")).lower()
    else:
        is_defined = None
        text = str(value).lower()
    refs = ["escalation_clause"]
    if is_defined is False:
        return RuleResult(rule_id="R2", verdict="FAIL", reason="Escalation clause is explicitly not defined", source_field_refs=refs)
    vague_markers = ("mutually agreed", "to be agreed", "at owner's discretion")
    has_mechanism = any(ch.isdigit() for ch in text) or "%" in text
    if any(marker in text for marker in vague_markers) and not has_mechanism:
        return RuleResult(
            rule_id="R2", verdict="FAIL",
            reason="Escalation clause has no defined mechanism or percentage",
            source_field_refs=refs,
        )
    if is_defined or has_mechanism:
        return RuleResult(rule_id="R2", verdict="PASS", reason="Escalation clause defines a mechanism", source_field_refs=refs)
    return _not_determinable("R2", "Escalation clause present but mechanism unclear", refs)


def check_r3(fields: dict[str, ExtractedField], units: dict[str, UnitRecord]) -> RuleResult:
    start = _field(fields, "start_date")
    end = _field(fields, "end_date")
    if start is None or end is None:
        return _not_determinable("R3", "start_date or end_date missing, term cannot be computed", ["start_date", "end_date"])
    term_months = _months_between(date.fromisoformat(start.value), date.fromisoformat(end.value))
    refs = ["start_date", "end_date"]
    if term_months <= 36:
        return RuleResult(rule_id="R3", verdict="PASS", reason=f"Term is {term_months} months", source_field_refs=refs)
    return RuleResult(rule_id="R3", verdict="FAIL", reason=f"Term is {term_months} months, exceeds 36", source_field_refs=refs)


def check_r4(fields: dict[str, ExtractedField], units: dict[str, UnitRecord]) -> RuleResult:
    start = _field(fields, "start_date")
    end = _field(fields, "end_date")
    if start is None or end is None:
        return _not_determinable("R4", "start_date or end_date missing", ["start_date", "end_date"])
    start_d, end_d = date.fromisoformat(start.value), date.fromisoformat(end.value)
    refs = ["start_date", "end_date"]
    if end_d <= start_d:
        return RuleResult(rule_id="R4", verdict="FAIL", reason="Expiry date is not after commencement date", source_field_refs=refs)
    computed = _months_between(start_d, end_d)
    stated = _field(fields, "term_months")
    if stated is not None:
        refs = [*refs, "term_months"]
        if int(stated.value) != computed:
            return RuleResult(
                rule_id="R4", verdict="FAIL",
                reason=f"Stated term ({stated.value} months) does not match dates ({computed} months)",
                source_field_refs=refs,
            )
    return RuleResult(rule_id="R4", verdict="PASS", reason=f"Expiry after commencement; term is {computed} months", source_field_refs=refs)


def check_r5(fields: dict[str, ExtractedField], units: dict[str, UnitRecord]) -> RuleResult:
    landlord = _field(fields, "landlord_name")
    tenant = _field(fields, "tenant_name")
    landlord_signed = _field(fields, "landlord_signed")
    tenant_signed = _field(fields, "tenant_signed")
    refs = ["landlord_name", "tenant_name", "landlord_signed", "tenant_signed"]
    if landlord is None or tenant is None:
        return _not_determinable("R5", "Landlord and/or tenant not identified in the document", refs)
    if landlord_signed is None or tenant_signed is None:
        return _not_determinable("R5", "Signature presence could not be determined from extracted text", refs)
    if landlord_signed.value and tenant_signed.value:
        return RuleResult(rule_id="R5", verdict="PASS", reason="Both parties identified and signed", source_field_refs=refs)
    return RuleResult(rule_id="R5", verdict="FAIL", reason="One or both parties have not signed", source_field_refs=refs)


def check_r6(fields: dict[str, ExtractedField], units: dict[str, UnitRecord]) -> RuleResult:
    rent = _field(fields, "rent_amount")
    freq = _field(fields, "rent_frequency")
    if rent is None or freq is None:
        return _not_determinable("R6", "rent_amount or rent_frequency missing", ["rent_amount", "rent_frequency"])
    if freq.value not in ("monthly", "annual"):
        return _not_determinable("R6", f"Unsupported rent frequency '{freq.value}'", ["rent_frequency"])
    rent_decimal = _money(rent)
    if rent_decimal is None:
        return _not_determinable("R6", "rent_amount is not a valid decimal amount", ["rent_amount"])
    refs = ["rent_amount", "rent_frequency"]
    annual_stated = _field(fields, "annual_rent")
    if freq.value == "monthly":
        computed_annual = rent_decimal * 12
        if annual_stated is not None:
            refs = [*refs, "annual_rent"]
            annual_decimal = _money(annual_stated)
            if annual_decimal is not None and annual_decimal != computed_annual:
                return RuleResult(
                    rule_id="R6", verdict="FAIL",
                    reason=f"Stated annual rent ({annual_decimal}) != monthly x 12 ({computed_annual})",
                    source_field_refs=refs,
                )
        return RuleResult(rule_id="R6", verdict="PASS", reason="Annual rent reconciles with monthly rent", source_field_refs=refs)
    # freq == annual: rent_amount already is the annual figure by construction.
    return RuleResult(rule_id="R6", verdict="PASS", reason="Rent is stated annually; reconciliation is by construction", source_field_refs=refs)


def check_r7(fields: dict[str, ExtractedField], units: dict[str, UnitRecord]) -> RuleResult:
    unit_field = _field(fields, "unit_id")
    if unit_field is None or unit_field.value not in units:
        return _not_determinable("R7", "Lease could not be confidently matched to a unit in units.json", ["unit_id"])
    unit = units[str(unit_field.value)]
    if unit.status == "available":
        return RuleResult(rule_id="R7", verdict="PASS", reason=f"Unit {unit.unit_id} exists and is available", source_field_refs=["unit_id"])
    return RuleResult(rule_id="R7", verdict="FAIL", reason=f"Unit {unit.unit_id} is not available (status: {unit.status})", source_field_refs=["unit_id"])


RULES = {
    "R1": check_r1,
    "R2": check_r2,
    "R3": check_r3,
    "R4": check_r4,
    "R5": check_r5,
    "R6": check_r6,
    "R7": check_r7,
}


def evaluate_rules(fields: list[ExtractedField], units: dict[str, UnitRecord]) -> list[RuleResult]:
    by_name = {f.field_name: f for f in fields}
    ruleset = load_ruleset()
    rule_ids = [rule["id"] for rule in ruleset["rules"]]
    return [RULES[rule_id](by_name, units) for rule_id in rule_ids if rule_id in RULES]
