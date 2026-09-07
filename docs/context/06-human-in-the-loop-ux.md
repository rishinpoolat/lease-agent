# Layer 06 — Human-in-the-Loop UX

Answers: *how does a human review, override, and connect the two features on
one screen?* (Requirements C1/C2 in [[01-requirements]].)

## Review state machine

Every `LeaseField`, `Flag`, and `WorkOrder` carries `review_status`:
`pending → accepted | rejected`, with `edited` as a variant of `accepted` for
`LeaseField` (see [[02-domain-model]] — `edited_value` is stored alongside the
original, never overwriting it).

- **Reject is non-destructive.** It marks the row reviewed-and-rejected; it
  never deletes the underlying extraction. The audit trail (what the agent
  said, what the human decided) must survive review either way — this is
  what "traceable and overridable" (per the brief's "what we're assessing")
  actually requires: both halves, not just the override.
- **Accepting a field with a bad value is what editing is for.** The reviewer
  edits the value, which sets `edited_value` and `review_status = edited` —
  the original agent output stays visible (e.g. struck through or in a
  "originally extracted" tooltip), not silently replaced.
- No confirmation dialog needed for reject (it's reversible in effect, since
  nothing is deleted); occupancy mutation (A4) is the one place a real
  confirmation matters, because it's a write to `Unit.status` that affects
  data outside the lease itself.

## Unit detail page — the "bringing them together" screen

One screen per unit, two panels, because this is the concrete answer to "how
you connect the two features around the unit":

- **Lease panel**: extracted fields (each with its `review_status` badge and,
  on click/hover, its `source_excerpt`), rule evaluation results (PASS/FAIL/
  NOT_DETERMINABLE badges, high severity first per [[03-validation-rules]]),
  and any document-level flags.
- **Issues panel**: photo reports and their draft work orders for this unit,
  each with its own review controls and a link back to the source photo(s).

Both panels read from the same `unit_id` — there is no separate "issues"
section elsewhere in the app; issues only exist in the context of a unit, per
the brief.

## Traceability affordance

- Clicking/hovering an extracted field highlights or shows its
  `source_excerpt` — the reviewer should never have to re-open the original
  PDF to sanity-check a value.
- Clicking a work order shows the photo(s) it was drafted from and the
  detected contents/damages that led to it.
- A field with `confidence = not_found` renders visibly empty/flagged, not
  hidden — a missing field is information (per A2), not a rendering gap.

## Badge conventions (keep consistent across the app)

| State | Meaning |
|-------|---------|
| `pending` (neutral) | Awaiting human review — the default for everything an agent produces |
| `accepted` (positive) | Human confirmed the agent's value as-is |
| `edited` (positive, distinct style) | Human confirmed but changed the value |
| `rejected` (negative) | Human rejected — record kept, not deleted |
| `PASS` / `FAIL` / `NOT_DETERMINABLE` | Rule verdicts — a separate badge family from review status; a field can be `accepted` and still feed a `FAIL` rule (e.g. reviewer confirms the deposit is genuinely too low) |

Don't conflate rule verdicts with review status — they answer different
questions (business-rule correctness vs. "did a human look at this").
