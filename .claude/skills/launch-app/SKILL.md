---
name: launch-app
description: How to start the full lease-agent stack locally and verify it end-to-end using the bundled fixtures. Use whenever asked to run, start, demo, or confirm the app works (not just pass its test suite) — this is the project-specific skill the general "run" skill looks for first.
---

# Launching and verifying lease-agent

No API key or external service is needed — everything (postgres, rabbitmq,
migration+seed, api, worker, web) comes up from one compose file.

## Start

```bash
docker compose up
```

Wait for the `migrate` service to exit 0 and `api`/`worker`/`web` to report
ready — `api` and `worker` both depend on `migrate` finishing first. If you
need a clean slate: `docker compose down -v` (drops the postgres volume,
so the next `up` reseeds `units.json` from scratch).

- Web: `http://localhost:3000`
- API: `http://localhost:8000`
- RabbitMQ management UI: `http://localhost:15672` (guest/guest) — use this
  to watch a job move through `lease.extraction`/`photo.analysis` and their
  DLQs if something looks stuck.

## Exercise the full pipeline

```bash
# Lease → extraction → rule engine → matched unit
curl -F "file=@fixtures/sample_lease.txt" http://localhost:8000/leases
# -> {"job_id": "..."}; poll until done:
curl http://localhost:8000/jobs/<job_id>

# Photos → condition assessment → draft work order, same unit
curl -F "files=@fixtures/sample_photos/unit-1204-ac-worn.png" \
     -F "files=@fixtures/sample_photos/unit-1204-water-heater-new.png" \
     -F "files=@fixtures/sample_photos/unit-1204-wall-damage.png" \
     http://localhost:8000/units/MC-B-1204/photos
```

Then open `http://localhost:3000/units/MC-B-1204`.

## What "working" looks like

- The unit page shows: extracted lease fields (each with a source excerpt
  on click), the R1–R7 rule table, flags, photo-derived issues, and a draft
  work order — all together, per `docs/context/06-human-in-the-loop-ux.md`.
- The fixture lease is written to genuinely FAIL rule **R4** (inclusive-end-
  date term) — if every rule shows PASS, extraction or the rule engine
  regressed; this is the one verdict that should NOT be green on unmodified
  fixtures.
- Accept/reject/edit works on fields, flags, and the work order; reject is
  non-destructive (original value still visible, not deleted).
- Occupancy on the unit only flips to `occupied` after accepting the
  lease-to-unit match **and** R7 shows PASS — never on upload alone.

## Known sharp edges (don't re-diagnose these from scratch)

- `docs/*.json` paths resolve differently in-container vs. on the host —
  see `backend/packages/agents/agents/paths.py` / `RULESET_JSON_PATH` /
  `UNITS_JSON_PATH` if a rule/unit lookup comes back empty inside Docker
  but works when running a package's tests on the host.
- `db/seed.py` never re-syncs `Unit.status` on restart (only inserts new
  units) — if occupancy looks reset after a `docker compose up` restart,
  that's a regression, not expected reseed behavior.

## Individual services (outside Docker)

See `CLAUDE.md`'s Commands section — `uv run uvicorn app.main:app --reload`
(api), `uv run python -m worker.main` (worker), `npm run dev` (web).
