# Layer 01 — Requirements & Scope

**Consult this layer first, before any implementation work.** It answers: *is this
in scope, and where does the requirement come from?*

## Authority hierarchy

1. `docs/solution-brief.md` — the this project brief itself, as sent by
   the property owner. This wins over everything below.
2. `docs/owner_ruleset.json` / `docs/units.json` — sample data contracts. Field
   names and shapes here are load-bearing; don't rename or restructure them.
3. This registry's scope decisions (Built / Deferred / Won't-do).
4. `README.md`'s "What I left out" section — the human-readable version of the
   Deferred/Won't-do rows below.

If a request conflicts with the brief, the brief wins — flag the conflict to the
developer rather than silently reinterpreting it.

## Requirement registry

| ID | Requirement (from brief) | Status | Notes |
|----|---------------------------|--------|-------|
| A1 | Extract structured lease fields (parties, unit, dates, rent amount+frequency, deposit, escalation, renewal, termination), each linked to its source in the document | Built | See [[02-domain-model]] for the field inventory + traceability contract |
| A2 | Flag problems a human should check (missing fields, contradictions, values that look wrong) | Built | Agent responsibility, not a rule-engine responsibility — see [[04-agent-boundaries]] |
| A3 | Validate against `owner_ruleset.json` — PASS / FAIL / NOT_DETERMINABLE + reason | Built | See [[03-validation-rules]] |
| A4 | Match lease to its unit in `units.json`, update occupancy | Built | Occupancy update is gated on R7 passing **and** human acceptance — see [[03-validation-rules]] |
| B1 | Assess condition from photos (new vs. worn/old, visible damage) | Built | Vision agent — see [[04-agent-boundaries]] |
| B2 | Identify visible contents/equipment (AC unit, water heater, appliances, fixtures) | Built | Same vision agent call as B1 |
| B3 | Draft work order (title, what's wrong, affected unit) | Built | Derived from B1+B2 output, not a separate model call |
| C1 | Lease + open issues visible together on one unit screen | Built | See [[06-human-in-the-loop-ux]] |
| C2 | Human accept/reject for every extracted field, flag, and draft work order | Built | See [[06-human-in-the-loop-ux]] — reject is non-destructive |
| G1 | No API key needed — stub text + vision models behind an interface | Built | See [[04-agent-boundaries]] |
| G2 | Document API requirements in the README so a real key can be dropped in | Built | README "Model providers" section |
| — | Auth / RBAC | Won't-do (this build) | Single implicit owner (Marina Crest Holdings), matches sample data scope. Named as a deliberate gap in README, with how-I'd-add-it notes, since the target role explicitly owns RBAC. See ADR-005 in [[07-decisions]] |
| — | Multi-tenant / multi-owner support | Deferred | Real product idea for README's "how I'd make this more useful," not built |
| — | Real (non-stub) model provider wiring | Deferred | Interface is provider-agnostic by design (ADR-003); swapping in a real key is a config change, not a rewrite |

## Classifying a new request

When a new feature/change is proposed, before planning it:

1. **Already in the registry as Built?** → it's a normal feature-checklist task
   against existing scope.
2. **Not in the registry, but it's a natural extension of A1–C2** (e.g. a new
   extracted field, a new rule, a new photo-detection category)? → this is a
   scope decision, not an implementation detail. Ask the developer: build it now
   (add a row, status Built) or park it as a README product idea (status
   Deferred)? Do not silently expand scope.
3. **Clearly outside the brief** (e.g. billing, tenant portal, multi-owner) →
   Deferred by default. Only becomes Built if the developer explicitly says so,
   at which point add a row here first.

Never delete a row — change its status and note why (link the ADR if the
decision has real rationale worth preserving).
