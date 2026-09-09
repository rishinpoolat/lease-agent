# Lease Agent

Two linked AI agents for a property owner, unified around a unit: one turns
an uploaded lease into a structured, validated, traceable record; one turns
uploaded photos into a condition assessment and a draft work order. Both
land on one unit screen with full human accept/reject/edit control.

**Status:** working end-to-end, verified via `docker compose up`. No real
sample lease/photos were available when this was built, so it runs against
a synthetic fixture lease + placeholder photos (`fixtures/`, clearly
labeled) — swapping in real data is a fixture change, not an architecture
change.

## How to run it

Requires Docker + Docker Compose. No API key needed.

```bash
docker compose up
```

This starts Postgres, RabbitMQ, a one-shot migration+seed job, the API
(`:8000`), the worker, and the frontend (`:3000`). Open `http://localhost:3000`.

Try the pipeline against the included fixtures:

```bash
# Upload the sample lease
curl -F "file=@fixtures/sample_lease.txt" http://localhost:8000/leases
# -> {"job_id": "..."} -- poll GET /jobs/{job_id} until status is "done",
# then open the matched unit (Apartment 1204, Tower B) at localhost:3000

# Report an issue with sample photos
curl -F "files=@fixtures/sample_photos/unit-1204-ac-worn.png" \
     -F "files=@fixtures/sample_photos/unit-1204-water-heater-new.png" \
     -F "files=@fixtures/sample_photos/unit-1204-wall-damage.png" \
     http://localhost:8000/units/MC-B-1204/photos
```

RabbitMQ's management UI is at `http://localhost:15672` (guest/guest) if you
want to watch jobs move through the queues.

Running services individually (outside Docker) is documented in `CLAUDE.md`
under Commands.

## Task summary

- **Part A — Lease record:** upload a lease → agent extracts structured
  fields (parties, unit, dates, rent, deposit, escalation, renewal/termination),
  each traceable to source text; flags problems; validates against
  `owner_ruleset.json` (PASS/FAIL/NOT_DETERMINABLE + reason); matches to a
  unit in `units.json`.
- **Part B — Issue reporting:** upload photo(s) of a unit → agent assesses
  condition, identifies visible contents/equipment, drafts a work order.
- Both come together on one unit view. Every extracted field, flag, and
  draft work order is human accept/reject/edit-able, and reject is
  non-destructive (the original agent output is kept, never deleted).
- Occupancy only flips to `occupied` after **both** rule R7 passes **and** a
  human explicitly accepts the unit match — never automatically.
- No live API key required — both the text and vision model calls are
  stubbed behind a `ModelProvider` interface.

Full brief: `docs/solution-brief.md` (kept locally, gitignored — not part
of this public repo).

## Architecture

Upload → API stores the file and enqueues a job (never calls a model
itself) → RabbitMQ decouples that from → a worker, which calls the
`ModelProvider` (extraction or vision), runs the R1–R7 rule engine for lease
jobs, and persists everything as provisional (`review_status = pending`,
always carrying a source reference) → a human reviews on the unit page.

This repo's `docs/context/` holds the full design as a set of authoritative,
numbered reference files (requirements/scope, domain model + traceability
contract, validation rules, agent boundaries, pipeline/queue architecture,
human-in-the-loop UX, and an ADR log) — this is also the context system
`CLAUDE.md` and `.claude/rules/context-layers.md` use to keep an AI coding
assistant consistent across a session instead of re-deriving the domain
every time. Worth a look if you want the reasoning behind the design, not
just the result: `docs/context/07-decisions.md` has every major call with
its rationale and rejected alternative.

Model requirements for a real (non-stub) provider: long-context + reliable
structured output for text, image input + structured output for vision —
see `docs/context/04-agent-boundaries.md`.

## Main decisions

Full rationale in `docs/context/07-decisions.md` (ADR-001 to ADR-008).
Highlights:

- **Python + FastAPI, async, with a RabbitMQ-backed worker** — model calls
  are slow and rate-limited; decoupling them from the request/response
  cycle is the concrete answer to "where would this break first at scale."
- **A hand-written `ModelProvider` interface, no agent framework** — the
  boundary design (only the worker calls it, every field carries a source
  reference or an explicit "not found") is the thing being assessed; a
  framework would obscure it.
- **The stub does real heuristic extraction, not canned output** — it runs
  regex/keyword heuristics over whatever text it's given and returns
  `source_excerpt` as a genuine substring of the input. It already behaves
  reasonably on a different lease, not just the fixture. The photo stub is
  more honestly a stub (it can't see pixels) — it keys off filename hints,
  documented as a limitation.
- **Lease fields stored as rows (EAV-style), not fixed columns** — every
  field needs independent confidence/source/review-status, and a new
  extracted field should be a data change, not a migration.
- **No auth/RBAC** — everything is scoped to one implicit owner matching
  the sample data; see "What I left out."

## What I left out

- **Auth/RBAC.** Single implicit owner. A real product needs at least
  owner/tenant/inspector roles — the review actions (accept/reject a lease
  field, a flag, a work order) are exactly where role checks would go.
- **A real model provider.** The interface is designed to make this a
  constructor swap (`backend/worker/worker/deps.py`), not a rewrite, but no
  live key is wired up.
- **Transactional outbox for job publishing.** The API commits the DB write
  then publishes to RabbitMQ; if the publish fails after commit, that job
  stays queued with no message in flight. The correct fix is an outbox
  table + relay process — noted in code (`backend/api/app/routers/leases.py`)
  rather than built, since it's a well-understood pattern that didn't seem
  worth the time budget for this project's current scope.
- **Hardened production Dockerfiles.** Current ones are dev-style
  (bind-mounted source, dev servers, no multi-stage build, no non-root
  user). Fine for local eval, not for deployment as-is.
- **Re-running validation after a human edits a field.** Right now R1–R7
  run once, at extraction time. If a reviewer corrects a wrong rent amount,
  the rule verdicts don't recompute — a real product would re-validate on
  edit.
- **Lease history / multiple leases per unit.** The unit page shows the
  most recently uploaded lease matched to that unit; older leases aren't
  browsable.
- **CI does not run integration tests against real Postgres/RabbitMQ** —
  only the pure-logic unit tests (rule engine, stub extraction, frontend
  component tests). A full docker-compose-based CI job is the natural next
  step (see `.github/workflows/ci.yml`).

## Where it would break first at scale

Roughly in order:

1. **The model provider's rate limit / cost**, not the infrastructure —
   once a real provider is wired in, worker throughput is bounded by
   whatever the provider allows, long before RabbitMQ or Postgres notice
   load. This is the reason the queue exists at all: it's the seam where
   you'd add worker autoscaling on queue depth.
2. **The publish-after-commit gap** above — under load, a failed publish
   after a successful commit becomes a real (if rare) stuck-job problem
   without an outbox.
3. **`LeaseField` as an EAV table** trades write simplicity for read cost —
   the unit-detail query aggregates rows into an object in the API layer.
   Fine at this project's scale; at real scale you'd want either a materialized
   view per lease or to accept the join cost is bounded (it is — one lease
   has on the order of 15 fields, not thousands).
4. **Local disk storage** — `Storage` is already an interface for exactly
   this reason (swap in GCS/S3), but as-shipped, uploaded files live on a
   single host's disk, which doesn't survive a multi-instance deployment.

## How I'd make this more useful

- **Confidence-driven review queues.** Instead of one flat list, surface
  "needs review" (low confidence, flagged, or a rule FAIL) separately from
  "looks fine, spot-check if you want" — most of a reviewer's time should
  go to the fields that actually need judgment.
- **Re-validate on edit** (see "What I left out") — closes the loop between
  human corrections and rule verdicts.
- **A real audit log**, not just `review_status` — who accepted/rejected
  what, when. This is a natural fit for an append-only store (e.g.
  Firestore) alongside Postgres, exactly the kind of addition
  `docs/context/07-decisions.md` (ADR-007) flags as reasonable *in addition
  to* the relational core, not a replacement for it.
- **Cross-lease consistency checks** — e.g. flag when a renewed lease's
  rent looks anomalous against the unit's own lease history, not just
  against the static ruleset. This is where "real agent" reasoning has the
  most room to grow past what a fixed rule engine can express.
- **Bulk intake.** Right now it's one lease / one photo batch per upload.
  A property owner onboarding a whole building wants to drop in a folder of
  leases and get a triage queue, not one-at-a-time uploads.
- **RBAC-scoped views** — a tenant reporting an issue shouldn't see the
  lease's rent/deposit fields; an inspector shouldn't approve their own
  finding. This is also where the interesting agent-boundary work is for a
  multi-tenant version of this product.

## Design goals

- Real agent behavior (reasoning over docs/images, validation,
  human-in-the-loop) vs. a form with an LLM attached
- Traceable, overridable outputs
- How the two features connect around the unit; code/data structure at scale
- Readable code + a clear README
