# Spec: Initial build — full working slice

## Problem
No application code exists yet. The architecture and Claude Code context
system (`docs/context/01`–`07`) are in place but unimplemented.

## Scope
Full end-to-end slice of requirements A1–A4, B1–B3, C1–C2, G1–G2 from
`docs/context/01-requirements.md`: lease upload → async extraction →
validation → unit match; photo upload → async condition assessment → draft
work order; unified unit view with human accept/reject/edit for every
extracted field, flag, and work order. Runs locally via `docker compose up`.

## Out of scope
Auth/RBAC, multi-tenancy, real (non-stub) model provider wiring, hardened
production Dockerfiles/CI — all per `docs/context/01` registry and ADR-005/
ADR-008 in `docs/context/07-decisions.md`.

## Context layers touched
All of them — this is the first implementation pass, so every layer's
contract gets exercised: 02 (schema), 03 (rule engine), 04 (agent
interface + stub), 05 (queue/worker), 06 (review UX). 01 and 07 get minor
edits (see below).

## Open questions and answers
- No real sample lease/photos exist yet → build synthetic fixtures now, full
  architecture against them (developer decision, see conversation).
- Duplicate brief files (`docs/Solution-brief-explained.docx` +
  `docs/solution-brief.md`) → keep the markdown only (developer decision).
- `docs/job_description.txt` → remove from the repo; it's the target
  company's own posting and shouldn't ship back to them as "context" for the
  stack choice (flagged and agreed during planning).

## Decisions made during this build
Recorded as they're made in `docs/context/07-decisions.md` (ADR-009+ if any
new ones arise beyond the eight already logged) rather than duplicated here.
