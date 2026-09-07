# Lease Agent — Claude Code Context

This project for the property owner: two linked AI agents for a property owner — one
that turns an uploaded lease into a structured, validated, traceable record,
one that turns uploaded photos into a condition assessment and a draft work
order — unified on a single per-unit screen with full human accept/reject
control. Full brief: `docs/solution-brief.md`.

Status: fully scaffolded and working end-to-end (verified via
`docker compose up` — upload → queue → worker → rule validation → unit view
→ human review, including the occupancy-flip gate). `CODEBASE_MAP.md`
describes the actual structure now, not a plan.

## Stack

- **API**: Python + FastAPI (`backend/api/`)
- **Worker**: Python, RabbitMQ consumer (`backend/worker/`) — the only place
  `ModelProvider` (the agent interface) is called from
- **Frontend**: Next.js (`frontend/`)
- **DB**: Postgres (lease fields stored as rows, not fixed columns — see
  ADR-006)
- **Queue**: RabbitMQ (`lease.extraction`, `photo.analysis`, + DLQs)
- **Shared Python packages** (`backend/packages/`): `agents/` (ModelProvider
  interface + stub + rule engine), `db/` (SQLAlchemy models + Alembic
  migrations), `storage/` (Storage interface + local-disk implementation,
  shared by api and worker)
- **Local dev**: `docker-compose.yml` — postgres, rabbitmq, migrate (one-shot
  migration+seed), api, worker, web
- **CI**: `.github/workflows/` — backend tests, frontend lint/test/build,
  and an AI PR reviewer

Why this stack: `docs/context/07-decisions.md` (ADR-001 through ADR-008).

## Architecture, in one paragraph

An upload (lease PDF/text or photos) hits the API, which stores the file and
enqueues a job — it never calls a model itself. A worker consumes the job,
calls the appropriate agent capability (`extract_lease` or `analyze_photos`)
behind the `ModelProvider` interface, and for lease jobs also runs the R1–R7
rule engine against `docs/owner_ruleset.json`. Every result — extracted
field, flag, rule verdict, draft work order — is written as provisional
(`review_status = pending`) with a source reference, never straight to
"fact." A human reviews and accepts/rejects/edits on the unit's detail page,
which is the one screen where a unit's lease and its open issues render
together. See `docs/context/05-pipeline-architecture.md` for the full flow
and the scaling story.

## Context layers (read before implementing)

This project's domain knowledge lives in `docs/context/`, one file per
concern, consulted in a defined cascade — see
`.claude/rules/context-layers.md` for the enforcement rule and a worked
example. Summary:

| # | File | Answers |
|---|------|---------|
| 01 | `docs/context/01-requirements.md` | What's in scope, built vs. deferred |
| 02 | `docs/context/02-domain-model.md` | Data shapes, traceability contract |
| 03 | `docs/context/03-validation-rules.md` | Rule engine, occupancy gating |
| 04 | `docs/context/04-agent-boundaries.md` | Agent interface, hard rules — **read this one first** |
| 05 | `docs/context/05-pipeline-architecture.md` | Queue flow, failure handling, scale |
| 06 | `docs/context/06-human-in-the-loop-ux.md` | Review states, unit view layout |
| 07 | `docs/context/07-decisions.md` | ADRs — why things are built this way |

`docs/owner_ruleset.json` and `docs/units.json` are sample data contracts,
read live at runtime (via `RULESET_JSON_PATH`/`UNITS_JSON_PATH` env vars in
Docker, or a repo-relative default in local dev — see
`backend/packages/agents/agents/paths.py`) — never copy their content into
code or docs.

## Commands

```bash
# Everything (postgres, rabbitmq, migrate, api, worker, web)
docker compose up

# --- Backend (from backend/) ---
uv sync --all-packages          # first time / after dependency changes
uv run pytest packages/agents/tests packages/db/tests packages/storage/tests -v

# api/tests and worker/tests need a real Postgres (occupancy-write gating,
# queue-redelivery idempotency) -- they skip automatically without this.
# Point TEST_DATABASE_URL at any disposable Postgres, e.g. a scratch DB on
# the docker-compose one: `docker compose exec postgres psql -U lease_agent
# -d lease_agent -c "CREATE DATABASE lease_agent_test"`, then:
TEST_DATABASE_URL="postgresql+asyncpg://lease_agent:lease_agent@localhost:5432/lease_agent_test" \
  uv run pytest api/tests worker/tests -v
# CI provides its own ephemeral Postgres service container for these — see
# .github/workflows/ci.yml.

# API only, from backend/api/
uv run uvicorn app.main:app --reload

# Worker only, from backend/worker/
uv run python -m worker.main

# DB migrations, from backend/packages/db/
uv run alembic upgrade head
uv run python -m db.seed

# --- Frontend (from frontend/) ---
npm install
npm run dev
npm test
npm run lint
npm run build
```

## Workflow

Every feature goes through plan mode with explicit developer approval before
any code is written. Plans and specs are per-feature (`specs/<date>-<name>/`),
not a single shared file.

**Always-loaded rules** (apply to nearly every task, see `.claude/rules/`):
- `.claude/rules/context-layers.md` — consult `docs/context/` before
  implementing anything touching fields, rules, agents, the queue, or review
  UX
- `.claude/rules/plan-mode.md` — the approval gate, mandatory

**On-demand skills** (loaded only when relevant, see `.claude/skills/`):
- `feature-checklist` — what to consider before/while planning a feature
- `testing` — mandatory test + review workflow after implementation
- `git-workflow` — branching conventions, where plans live
- `codebase-map` — when/how to update `CODEBASE_MAP.md`

Skills are auto-discovered by Claude when a task matches their description,
so they don't cost context until actually needed.

**Navigation**: Prefer `CODEBASE_MAP.md` over re-scanning directories; only
grep/read when the map doesn't answer the question.

## What's deliberately not built

No auth/RBAC, no multi-tenancy, no real (non-stub) model provider wiring by
default, no hardened production Dockerfiles (dev-style bind-mount images
only). Each is a named, reasoned decision — see
`docs/context/01-requirements.md` (registry) and `docs/context/07-decisions.md`
(ADR-005/ADR-008) — not an oversight. Don't build these without an explicit
developer request that updates the requirements registry first.
