# Plan: Initial build — full working slice

Spec: `spec.md` in this folder. Full design rationale:
`docs/context/*.md`.

Note: mid-build, the developer asked to split `backend/`/`frontend/` into
separate top-level folders (originally planned as `apps/api`, `apps/worker`,
`apps/web`, `packages/*` at the repo root) — this plan's paths were updated
to match. See `docs/context/07-decisions.md` and `CODEBASE_MAP.md` for the
final structure.

## To Do
- (none — see Completed)

## In Progress
- (none)

## Completed
- [x] Housekeeping: removed duplicate docx, removed job_description.txt, scrubbed references
- [x] Repo scaffold: uv workspace (`backend/`), Next.js app (`frontend/`), `.gitignore`, `.env.example`
- [x] `backend/packages/db` — models (EAV `LeaseField`, enum fix via `type_annotation_map`), Alembic migration, seed script
- [x] `backend/packages/agents` — schemas, `ModelProvider` protocol, stub (heuristic extraction + filename-hint photo analysis), rule engine (R1–R7) + 19 unit tests
- [x] `backend/packages/storage` — added mid-build once it was clear the worker needed the same `Storage` interface as the API, not just the API (see ADR-008)
- [x] `fixtures/` — synthetic lease + photo placeholders, clearly labeled as sample data
- [x] `backend/api` — storage wiring, routers (units/leases/photos/jobs/review), RabbitMQ publisher
- [x] `backend/worker` — consumer, both handlers, bounded retry → dead-letter, idempotent redelivery
- [x] `frontend` — unit list/detail, upload flows with job polling, shared `ReviewControl` component, 6 component tests
- [x] `docker-compose.yml` + Dockerfiles (dev-style) — verified with a full `docker compose up`
- [x] Manual end-to-end verification via the running stack: lease upload → extraction → R1–R7 evaluation (including a genuine R4 FAIL on the fixture's inclusive-end-date term) → field/unit-match review → occupancy flip gated on R7 PASS + acceptance; photo upload → condition assessment → draft work order, both visible on the same unit
- [x] CI/CD: `.github/workflows/ci.yml` (backend + frontend), `.github/workflows/ai-pr-review.yml`
- [x] Updated `CODEBASE_MAP.md`, `CLAUDE.md`, `.claude/agents/*`, `docs/context/04`, `fixtures/README.md` for the final `backend/`/`frontend/` structure
- [x] README run instructions

## Test plan (executed)
- Unit tests: rule engine (all 3 verdicts across representative rules),
  stub extraction heuristics against the fixture lease, stub photo analysis
  filename-hint matching — `backend/packages/agents/tests/`.
- Frontend: `ReviewControl` state-transition tests — `frontend/tests/`.
- Manual: full docker-compose flow (see Completed above) — this caught two
  real bugs before they'd have shipped: a Docker-only `docs/*.json` path
  resolution bug (fixed via `agents/paths.py` env-var overrides) and a
  SQLAlchemy enum-value mismatch that broke seeding (fixed via
  `db/base.py`'s `type_annotation_map`).
