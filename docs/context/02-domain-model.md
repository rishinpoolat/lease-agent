# Layer 02 — Domain Model & Traceability

Answers: *what does the data look like, and what does every field owe the
human reviewing it?*

## The traceability contract (non-negotiable, per [[01-requirements]] A1/C2)

Every value the system extracts from a lease or infers from a photo is a
**claim**, not a fact, until a human accepts it. Concretely, every extracted
field carries:

- `value` — the extracted value (typed).
- `confidence` — `high` / `low` / `not_found` (drives whether the agent should
  also raise a flag — see [[04-agent-boundaries]]).
- `source_excerpt` — verbatim text span from the lease the value was read from
  (or `null` if not found). For photo-derived facts, `source_photo_id` +
  optional bounding box instead.
- `review_status` — `pending` / `accepted` / `rejected` / `edited`.
- `edited_value` — set only when a human overrides the extracted value.
  **Never overwrite `value` in place** — keep both so the original agent
  output stays auditable even after a correction (ADR-006 depends on this).

This is why lease fields are modeled as **rows, not columns** — see below.

## Core entities

### `Unit` (mirrors `units.json`)
`unit_id`, `property_id`, `building_id`, `label`, `type`, `area_sqm`,
`parking_bay`, `status` (`available` / `occupied`). Loaded from `units.json` as
seed data; `status` is mutated by A4 once a lease is matched and accepted.

### `Lease`
One per uploaded lease document. `id`, `source_file_ref`, `unit_id` (nullable
until matched), `uploaded_at`, `extraction_job_id`.

### `LeaseField` (EAV-style — see ADR-006)
One row per extracted field per lease: `lease_id`, `field_name` (e.g.
`rent_amount`, `rent_frequency`, `deposit_amount`, `escalation_clause`,
`landlord_name`, `tenant_name`, `start_date`, `end_date`, `term_months`,
`renewal_terms`, `termination_terms`), `value`, `confidence`,
`source_excerpt`, `review_status`, `edited_value`.

Adding a new extracted field later (e.g. a late-fee clause) is a new row kind,
not a schema migration — this is the payoff of the EAV shape.

### `Flag`
Problems the agent itself notices (not rule failures): `lease_id`,
`field_name` (nullable — some flags are document-level, e.g. "pages appear out
of order"), `description`, `severity`, `review_status`.

### `RuleEvaluation`
One row per `owner_ruleset.json` rule per lease: `lease_id`, `rule_id` (`R1`
… `R7`), `verdict` (`PASS` / `FAIL` / `NOT_DETERMINABLE`), `reason`,
`source_field_refs` (which `LeaseField` rows it relied on). Never duplicate
the rule's `description`/`check` text here — always read it live from
`owner_ruleset.json` (see [[03-validation-rules]]).

### `PhotoReport`
`id`, `unit_id`, `uploaded_at`, `photo_refs[]`, `condition_assessment` (free
text + structured tags, e.g. `worn`, `damaged`), `detected_contents[]` (e.g.
`AC unit`, `water heater`), `analysis_job_id`.

### `WorkOrder`
`id`, `photo_report_id`, `unit_id`, `title`, `description`, `severity`,
`review_status`.

### `Job`
Tracks async work (see [[05-pipeline-architecture]]): `id`, `type`
(`lease_extraction` / `photo_analysis`), `status` (`queued` / `processing` /
`done` / `failed`), `error`, `created_at`, `completed_at`.

## Why Postgres, not NoSQL

`Unit ↔ Lease ↔ LeaseField ↔ RuleEvaluation` and `Unit ↔ PhotoReport ↔
WorkOrder` are genuinely relational — the entire point of [[01-requirements]]
C1 is that a unit's lease and its open issues render together from one query.
A document store would just reimplement joins in application code. See
ADR-007.
