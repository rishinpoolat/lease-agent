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
- [x] Quality gate: dispatched `test-runner` + `code-reviewer` per
  `.claude/skills/testing`. code-reviewer found 2 blockers (path traversal
  in `LocalDiskStorage.save` via unsanitized upload filenames; money handled
  as `float` instead of `Decimal` throughout the rule engine/stub) and 3
  minor findings (no confirm() on the one occupancy-mutating UI action; no
  test coverage for occupancy-write gating or worker idempotency; R2/R5
  untested directly) — all fixed. Fixing the coverage gap surfaced a real
  latent bug of its own (`session.get(..., options=[selectinload(...)])`
  silently skips those options on an identity-map hit, which only mattered
  once a test reused one session across setup+call the way production never
  does) and, separately, manual re-verification surfaced that `db/seed.py`
  was reverting live occupancy changes on every restart — both fixed with
  regression tests. See `docs/context/07-decisions.md` if any of these
  warranted a new ADR (money-as-Decimal and the path-traversal fix are
  correctness/security fixes, not architecture decisions, so no new ADR).

## Test plan (executed)
- Unit tests: rule engine (all 7 rules, all applicable verdicts), stub
  extraction heuristics against the fixture lease, stub photo analysis
  filename-hint matching, storage path-traversal handling, seed reseed
  behavior — `backend/packages/{agents,db,storage}/tests/`. 35 tests.
- Integration tests (real Postgres, skip without `TEST_DATABASE_URL`):
  worker redelivery idempotency, occupancy-write gating (R7 PASS + human
  acceptance, both required) — `backend/{worker,api}/tests/`. 4 tests. CI
  runs these for real via a Postgres service container.
- Frontend: `ReviewControl` state-transition tests — `frontend/tests/`. 6 tests.
- Manual: full docker-compose flow (see Completed above) — this caught two
  real bugs before they'd have shipped: a Docker-only `docs/*.json` path
  resolution bug (fixed via `agents/paths.py` env-var overrides) and a
  SQLAlchemy enum-value mismatch that broke seeding (fixed via
  `db/base.py`'s `type_annotation_map`); a later manual restart caught the
  seed/occupancy-revert bug above.
