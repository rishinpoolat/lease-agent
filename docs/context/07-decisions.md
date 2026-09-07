# Layer 07 — Architecture Decisions (ADRs)

Resolved decisions with rationale. Consult before re-litigating a choice —
these are enforced on new work without re-asking, the same way the MSI HRMS
project's ADR-004/ADR-002 were.

---

### ADR-001: Python + FastAPI for the backend
**Decision**: Backend (API + worker) is Python, framework FastAPI.
**Why**: This is the stack I'd genuinely reach for to ship agent features
into production — async support that pairs naturally with a queue-backed
worker, Pydantic giving typed structured output for the agent layer for
free, and a language ecosystem where the model/vision SDKs, PDF/image
tooling, and background-worker patterns are all first-class. The brief
explicitly invites "whatever stack you'd genuinely reach for," and for a
production agentic pipeline (not a CRUD app) that's Python over Node.
**Alternative considered**: Node/Express + TypeScript (matches the repo's
original stale README default) — rejected, weaker fit for the agent/queue
core of this system.

### ADR-002: Next.js for the frontend
**Decision**: Frontend is Next.js (App Router).
**Why**: Server components suit the read-heavy unit-detail view (lease +
rule evaluations + issues joined server-side), and it's the standard choice
for a product-facing SaaS frontend with room to grow past "minimal UI."
**Alternative considered**: React + Vite — simpler to scaffold, reasonable
for a pure SPA, but Next.js is the better fit once this is treated as a real
product surface rather than a this project demo.

### ADR-003: Custom `ModelProvider` interface, not LangChain/LangGraph
**Decision**: Agents are a hand-written interface + stub implementation (see
[[04-agent-boundaries]]), no agent framework dependency.
**Why**: The brief only requires "stub the model behind an interface" — a
framework adds a dependency without adding a requirement. Owning the agent
boundary directly (rather than inheriting one from a framework's abstraction)
is also exactly the kind of design decision this build is meant to
demonstrate — a framework would obscure it.
**Alternative considered**: LangChain/LangGraph — rejected for this reason,
revisit only if the project later needs multi-step tool-calling loops a
hand-rolled interface can't express cleanly.

### ADR-004: RabbitMQ-backed async worker, not synchronous model calls
**Decision**: Uploads enqueue a job; a separate worker process calls the
model and persists results (see [[05-pipeline-architecture]]).
**Why**: Model calls are slow and rate-limited; coupling them to the
request/response cycle blocks the API and doesn't scale independently. This
is also the concrete answer to the brief's "where would this break first at
scale" question — a queue gives a real answer instead of a hypothetical one.
**Alternative considered**: synchronous in-request call — simpler, fine for a
pure demo, rejected because "production-level" was an explicit goal.

### ADR-005: No auth/multi-tenancy in this build
**Decision**: Single implicit owner (Marina Crest Holdings), no login, no
RBAC.
**Why**: All sample data (`owner_ruleset.json`, `units.json`) is scoped to
one ownership entity; the brief says "minimal UI is fine, we're not judging
visual design" and doesn't ask for auth. Building it would spend the 4-day
budget on something not assessed. Named explicitly in the README as a
deliberate gap with a short "how I'd add it" note — a real property-owner
product would need RBAC (owner vs. tenant vs. inspector, at minimum), so the
gap is worth naming, not hiding.
**Alternative considered**: basic single-user JWT auth — rejected as
budget-not-well-spent for this scope.

### ADR-006: Lease fields stored as rows (EAV-style), not fixed columns
**Decision**: `LeaseField` is one row per field per lease, not
`rent_amount`/`deposit_amount`/... columns on `Lease`.
**Why**: Every field needs independent `confidence`, `source_excerpt`, and
`review_status` (per [[02-domain-model]]'s traceability contract) — modeling
that as parallel columns (`rent_amount_confidence`, `rent_amount_source`, …)
multiplies the schema for every field and makes adding a new extracted field
a migration. Row-based storage makes it a data change instead. Trade-off:
queries that need "the whole lease as one object" require an aggregation
step in the API layer — acceptable, since the unit-detail view is the only
place that needs it, and the human-review UI (accept/reject per field) is
naturally row-shaped anyway.
**Alternative considered**: fixed columns — simpler queries, rejected because
it doesn't scale to new fields or per-field provenance without migrations.

### ADR-007: Postgres, not a document/NoSQL store
**Decision**: Postgres for everything, including `LeaseField` rows.
**Why**: `Unit ↔ Lease ↔ LeaseField ↔ RuleEvaluation` and `Unit ↔
PhotoReport ↔ WorkOrder` are relational by nature — the entire "bringing them
together" requirement (C1) is a join. A document store would just
reimplement referential integrity in application code.
**Alternative considered**: NoSQL (e.g. Firestore) — reasonable for a real
product's event/audit log, not for the core relational model; worth naming
as a future addition (e.g. an append-only audit log collection) in the
README's "how I'd make this more useful," not a replacement for Postgres
here.

### ADR-008: Storage behind an interface, local disk for this build
**Decision**: File uploads (lease PDFs, photos) go through a `Storage`
interface; the implementation used here is local disk.
**Why**: Mirrors the `ModelProvider` pattern (ADR-003) — keep the swap-in-a-
real-backend seam explicit rather than hardcoding a cloud SDK call inline. A
cloud object store (GCS/S3) is the natural production target, but wiring a
real bucket isn't necessary to demonstrate the boundary.
