# Context Layer Cascade

This project uses a layered context system, one authoritative file per
concern, under `docs/context/`. **Before implementing anything that touches
extracted fields, validation rules, agent behavior, the job/queue pipeline,
or review UX, consult the relevant layers in order — don't guess at an
answer one of them already gives.**

## The layers

| # | Layer | File | Answers |
|---|-------|------|---------|
| 01 | Requirements & Scope | `docs/context/01-requirements.md` | Is this in scope? Built, deferred, or won't-do? |
| 02 | Domain Model & Traceability | `docs/context/02-domain-model.md` | What does the data look like? What does every field owe the reviewer? |
| 03 | Validation Rules | `docs/context/03-validation-rules.md` | How does `owner_ruleset.json` map to PASS/FAIL/NOT_DETERMINABLE and occupancy? |
| 04 | Agent Boundaries | `docs/context/04-agent-boundaries.md` | What can an agent do, what must it return, where does it run? |
| 05 | Pipeline & Queue Architecture | `docs/context/05-pipeline-architecture.md` | How does an upload become a result? Failure/retry/scale story? |
| 06 | Human-in-the-Loop UX | `docs/context/06-human-in-the-loop-ux.md` | How does review/override/unit-view work? |
| 07 | Decisions (ADRs) | `docs/context/07-decisions.md` | Why was it built this way — is this settled? |

Plus `CODEBASE_MAP.md` (root) — search-first: check what already exists
before adding something that duplicates it.

## When to run the cascade

Any of: a new extracted lease field, a new validation rule or change to how
rules are checked, a new agent capability or prompt/schema change, a new job
type or change to queue topology, a new review/accept-reject interaction, or
any request that isn't obviously covered by existing code. Small, purely
mechanical changes (fixing a typo, a UI style tweak with no behavior change)
don't need the full cascade — use judgment, but default to running it when
unsure.

## Worked example: adding a new extracted field (`late_fee_clause`)

**01 — Requirements**: Is `late_fee_clause` in the registry? No — A1 lists
parties/unit/dates/rent/deposit/escalation/renewal/termination, not late
fees. → This is a scope decision: ask the developer whether to add it as
Built (add a row to the registry) or leave it as a README product idea. Say
the developer approves adding it now.

**02 — Domain model**: Add `late_fee_clause` to the `LeaseField` inventory —
type (text), traceability requirement (same as every field: value,
confidence, source_excerpt). No schema migration needed — `LeaseField` is
row-based (ADR-006), so this is a data change, not a code change to the
table shape.

**03 — Validation rules**: Does any rule in `owner_ruleset.json` reference
late fees? No (R1–R7 don't). No rule-engine change. Note: if the ruleset
later adds a rule that does, this field is already there to support it.

**04 — Agent boundaries**: Extend the extraction schema/prompt in the
`ModelProvider` (and the stub implementation) to emit `late_fee_clause` with
a source span, same shape as every other field. Consider whether an unusual
late-fee value should trigger a flag (per the agent's flag-raising
responsibility) — e.g. a fee that looks like a percentage stored as if it
were a flat amount.

**05 — Pipeline**: No queue/topology change — it's the same lease-extraction
job, one more field in the result the worker persists.

**06 — UX**: Renders on the unit view's lease panel as another field row,
same accept/reject/edit convention as existing fields, same source-highlight
behavior on click.

**07 — Decisions**: No new ADR needed — this is exactly the case ADR-006
was written to make cheap. If it *had* required a migration, that would be a
signal ADR-006 needs revisiting, and that's worth flagging to the developer.

**Result**: one registry row, one domain-model table row, one prompt/schema
update, one UI row-rendering — no query pipeline changes, no migration,
because the layers were followed instead of improvised.

## Rule

Don't propose an implementation for anything in the "when to run the
cascade" list without having read the relevant layer files first. If a layer
file doesn't answer the question, that's a gap — ask the developer, then
update the layer file with the answer so the next request doesn't hit the
same gap.
