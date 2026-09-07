"""The default ModelProvider — a first-class implementation, not a shortcut.

`extract_lease` runs real regex/keyword heuristics over the *actual* input
text and returns source_excerpt as a genuine substring of that text, so it
behaves reasonably on any similarly-structured lease, not just the fixture.
`analyze_photos` is a more honest stub — it can't see pixels, so it keys off
filename hints with a documented generic fallback. Both limitations, and why
they're acceptable for this build, are described in
docs/context/04-agent-boundaries.md.
"""

import re
from dataclasses import dataclass

from agents.provider import ImageRef
from agents.schemas import (
    ExtractedField,
    FlagCandidate,
    LeaseExtractionResult,
    PhotoAssessmentResult,
    WorkOrderDraft,
)
from agents.units_lookup import load_unit_labels

# ---------------------------------------------------------------------------
# Lease extraction
# ---------------------------------------------------------------------------

_MONEY = r"([\d,]+(?:\.\d+)?)"


def _money(text: str) -> float | None:
    return float(text.replace(",", "")) if text else None


def _paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def _paragraph_after_heading(text: str, heading_keyword: str) -> str | None:
    for para in _paragraphs(text):
        lines = para.splitlines()
        if lines and heading_keyword.lower() in lines[0].lower():
            body = "\n".join(lines[1:]).strip()
            return body or None
    return None


def _not_found(field_name: str) -> ExtractedField:
    return ExtractedField(field_name=field_name, value=None, confidence="not_found", source_excerpt=None)


def _found(field_name: str, value, source_excerpt: str) -> ExtractedField:
    return ExtractedField(field_name=field_name, value=value, confidence="high", source_excerpt=source_excerpt.strip())


def _extract_party(text: str, label: str, field_name: str) -> ExtractedField:
    match = re.search(rf"{label}:\s*([^,\n]+)", text)
    if not match:
        return _not_found(field_name)
    return _found(field_name, match.group(1).strip(), match.group(0))


def _extract_unit(text: str) -> ExtractedField:
    for unit in load_unit_labels():
        if unit.label.lower() in text.lower():
            idx = text.lower().find(unit.label.lower())
            excerpt = text[max(0, idx - 20) : idx + len(unit.label) + 40].strip()
            return _found("unit_id", unit.unit_id, excerpt)
    return _not_found("unit_id")


def _extract_dates(text: str) -> tuple[ExtractedField, ExtractedField, ExtractedField]:
    start = re.search(r"commence[sd]?\s+on\s+(\d{4}-\d{2}-\d{2})", text, re.IGNORECASE)
    end = re.search(r"terminate[sd]?\s+on\s+(\d{4}-\d{2}-\d{2})", text, re.IGNORECASE)
    term = re.search(r"total term of\s+(\d+)\s*months?", text, re.IGNORECASE)
    start_field = _found("start_date", start.group(1), start.group(0)) if start else _not_found("start_date")
    end_field = _found("end_date", end.group(1), end.group(0)) if end else _not_found("end_date")
    term_field = (
        _found("term_months", int(term.group(1)), term.group(0)) if term else _not_found("term_months")
    )
    return start_field, end_field, term_field


def _extract_rent(text: str) -> tuple[ExtractedField, ExtractedField, ExtractedField]:
    monthly = re.search(rf"rent of QAR\s*{_MONEY}\s*per month", text, re.IGNORECASE)
    annual = re.search(rf"annual rent under this Agreement is\s*QAR\s*{_MONEY}", text, re.IGNORECASE)
    if monthly:
        amount_field = _found("rent_amount", _money(monthly.group(1)), monthly.group(0))
        freq_field = _found("rent_frequency", "monthly", monthly.group(0))
    else:
        amount_field = _not_found("rent_amount")
        freq_field = _not_found("rent_frequency")
    annual_field = (
        _found("annual_rent", _money(annual.group(1)), annual.group(0)) if annual else _not_found("annual_rent")
    )
    return amount_field, freq_field, annual_field


def _extract_deposit(text: str) -> ExtractedField:
    match = re.search(rf"security deposit of QAR\s*{_MONEY}", text, re.IGNORECASE)
    if not match:
        return _not_found("deposit_amount")
    return _found("deposit_amount", _money(match.group(1)), match.group(0))


def _extract_escalation(text: str) -> ExtractedField:
    body = _paragraph_after_heading(text, "RENT ESCALATION")
    if not body:
        return _not_found("escalation_clause")
    has_mechanism = "%" in body or any(ch.isdigit() for ch in body)
    return _found(
        "escalation_clause",
        {"is_defined": has_mechanism, "mechanism_text": body},
        body,
    )


def _extract_terms(text: str) -> tuple[ExtractedField, ExtractedField]:
    renewal = _paragraph_after_heading(text, "RENEWAL")
    termination = _paragraph_after_heading(text, "TERMINATION")
    renewal_field = _found("renewal_terms", renewal, renewal) if renewal else _not_found("renewal_terms")
    termination_field = (
        _found("termination_terms", termination, termination) if termination else _not_found("termination_terms")
    )
    return renewal_field, termination_field


def _extract_signature(text: str, label: str, field_name: str) -> ExtractedField:
    match = re.search(rf"{label} Signature:\s*([^\n]+?)\s{{2,}}Date:", text)
    signed = bool(match and match.group(1).strip())
    if not match:
        return _not_found(field_name)
    return _found(field_name, signed, match.group(0))


def _flags_for(fields: list[ExtractedField]) -> list[FlagCandidate]:
    by_name = {f.field_name: f for f in fields}
    flags: list[FlagCandidate] = []

    important = {
        "landlord_name": "high",
        "tenant_name": "high",
        "unit_id": "high",
        "start_date": "high",
        "end_date": "high",
        "rent_amount": "high",
        "deposit_amount": "medium",
    }
    for name, severity in important.items():
        field = by_name.get(name)
        if field is None or field.confidence == "not_found":
            flags.append(
                FlagCandidate(field_name=name, description=f"'{name}' could not be found in the document", severity=severity)
            )

    start, end = by_name.get("start_date"), by_name.get("end_date")
    if start and end and start.value and end.value and end.value <= start.value:
        flags.append(
            FlagCandidate(field_name="end_date", description="End date is not after start date", severity="high")
        )

    rent = by_name.get("rent_amount")
    if rent and rent.value is not None and not (100 <= float(rent.value) <= 100_000):
        flags.append(
            FlagCandidate(field_name="rent_amount", description=f"Rent amount {rent.value} looks outside a plausible range", severity="medium")
        )

    return flags


@dataclass
class StubModelProvider:
    """See module docstring — this is the default ModelProvider."""

    def extract_lease(self, document_text: str) -> LeaseExtractionResult:
        fields: list[ExtractedField] = []
        fields.append(_extract_party(document_text, "Landlord", "landlord_name"))
        fields.append(_extract_party(document_text, "Tenant", "tenant_name"))
        fields.append(_extract_unit(document_text))
        start_field, end_field, term_field = _extract_dates(document_text)
        fields.extend([start_field, end_field, term_field])
        rent_field, freq_field, annual_field = _extract_rent(document_text)
        fields.extend([rent_field, freq_field, annual_field])
        fields.append(_extract_deposit(document_text))
        fields.append(_extract_escalation(document_text))
        fields.extend(_extract_terms(document_text))
        fields.append(_extract_signature(document_text, "Landlord", "landlord_signed"))
        fields.append(_extract_signature(document_text, "Tenant", "tenant_signed"))

        return LeaseExtractionResult(fields=fields, flags=_flags_for(fields))

    def analyze_photos(self, images: list[ImageRef]) -> PhotoAssessmentResult:
        content_hints = {
            "ac": "AC unit",
            "aircon": "AC unit",
            "water-heater": "water heater",
            "water_heater": "water heater",
            "fridge": "refrigerator",
            "wall": "wall/paint finish",
            "floor": "flooring",
            "fixture": "fixture",
            "appliance": "appliance",
        }
        condition_hints = {
            "worn": "worn",
            "old": "worn",
            "damage": "damaged",
            "damaged": "damaged",
            "broken": "damaged",
            "new": "new",
        }

        detected_contents: list[str] = []
        damages: list[str] = []
        conditions_seen: list[str] = []

        for image in images:
            normalized = re.sub(r"[-_.]", " ", image.filename.lower())
            content = next(
                (label for key, label in content_hints.items() if key.replace("-", " ").replace("_", " ") in normalized),
                "unspecified equipment",
            )
            condition = next(
                (label for key, label in condition_hints.items() if key.replace("-", " ").replace("_", " ") in normalized),
                None,
            )

            if content not in detected_contents:
                detected_contents.append(content)
            if condition:
                conditions_seen.append(condition)
                if condition in ("worn", "damaged"):
                    damages.append(f"{content} appears {condition}")

        if not images:
            return PhotoAssessmentResult(
                condition_assessment="No photos provided.",
                detected_contents=[],
                damages=[],
                draft_work_order=None,
            )

        if damages:
            summary = f"{len(damages)} of {len(images)} item(s) show visible wear or damage."
        else:
            summary = "No visible damage detected; items appear new or in good condition."
        condition_assessment = summary

        draft_work_order = None
        if damages:
            severity = "high" if any("damaged" in d for d in damages) else "medium"
            draft_work_order = WorkOrderDraft(
                title=f"Inspect and address: {', '.join(detected_contents)}",
                description="; ".join(damages),
                severity=severity,
            )

        return PhotoAssessmentResult(
            condition_assessment=condition_assessment,
            detected_contents=detected_contents,
            damages=damages,
            draft_work_order=draft_work_order,
        )
