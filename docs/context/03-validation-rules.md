# Layer 03 — Validation Rules

Answers: *how does `owner_ruleset.json` become PASS / FAIL / NOT_DETERMINABLE
output, and how does that connect to occupancy?* (Requirement A3/A4 in
[[01-requirements]].)

## Single source of truth

`docs/owner_ruleset.json` (R1–R7) is never copied or re-described in code.
Rule text, severity, and `check` expressions are read from that file at
runtime (or loaded once at startup) — code maps each `id` to a check
function, nothing more. If the ruleset file changes, no code change should be
required unless a genuinely new kind of check is introduced.

## Rule → function mapping

| Rule | Check (from ruleset) | Depends on `LeaseField`s | NOT_DETERMINABLE when |
|------|----------------------|---------------------------|------------------------|
| R1 | `deposit_amount >= monthly_rent` | `deposit_amount`, `rent_amount` (+ `rent_frequency == monthly`) | either field missing/low-confidence, or rent isn't monthly-denominated and can't be normalized |
| R2 | `escalation_clause.is_defined == true` | `escalation_clause` | escalation clause text missing/unreadable |
| R3 | `term_months <= 36` | `term_months` (derived from R4) | dates missing so term can't be computed |
| R4 | `expiry_date > commencement_date AND term_months == months_between(...)` | `start_date`, `end_date` | either date missing |
| R5 | both parties present + signed | `landlord`, `tenant` (+ signature detection) | signature presence can't be determined from the source (common — text extraction often can't see signatures) |
| R6 | `annual_rent == monthly_rent * 12` | `rent_amount`, `rent_frequency` | rent frequency isn't monthly/annual, or amount missing |
| R7 | unit exists in `units.json` AND `status == available` | `unit_id` (matched, not extracted verbatim — see below) | unit couldn't be confidently matched to any `units.json` entry |

Each check function returns `(verdict, reason, source_field_refs)` — `reason`
must name the specific missing/conflicting thing when the verdict isn't PASS,
not a generic "could not determine."

## R7 and occupancy (A4)

R7 is the one rule that reaches outside the lease into `units.json`. The unit
match (matching the lease's extracted unit reference to a `units.json`
`unit_id`) is itself a claim with its own confidence — treat it like any
other extracted field, not a guaranteed lookup.

**Occupancy update sequence**, in order:
1. Agent extracts a unit reference from the lease text (part of `LeaseField`,
   `field_name = "unit_id"`).
2. Worker attempts to match it to a `units.json` entry. No match / ambiguous
   match → R7 = `NOT_DETERMINABLE`, occupancy untouched.
3. Match found → R7 checks `status == 'available'`.
4. Occupancy is only flipped to `occupied` after **both** R7 = PASS **and** a
   human has accepted the lease-to-unit match in review — never on R7 PASS
   alone. This is the direct application of [[01-requirements]] C2 ("human
   should be able to accept or reject") to a state mutation, which is the
   highest-stakes kind of write in this system.

## Severity

`owner_ruleset.json`'s `severity` (`high` / `medium` / `low`) drives display
order and badge styling in the unit view ([[06-human-in-the-loop-ux]]) — high
severity FAILs surface first. Severity never changes verdict logic; it's
presentation only.
