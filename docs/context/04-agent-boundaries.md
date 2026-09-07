# Layer 04 — Agent Boundaries

Answers: *what is an agent allowed to do, what must it return, and where does
it live in the system?* This is the layer that makes A1/A2/B1/B2/B3 "real
agents" rather than a form with an LLM attached (per [[01-requirements]]) —
treat it as the most important layer in this project.

## Why these are agents, not forms

A form-with-LLM pattern would be: send the lease text to a model, ask for JSON,
save it. What makes this an *agent* instead:

- It **reasons over unstructured input** (document text / images), not a
  pre-defined form the user fills in.
- It **produces its own judgment calls** — confidence per field, and flags for
  problems nobody told it to look for (contradictions, values that look wrong,
  ambiguous condition assessments) — not just extraction.
- Its output is **provisional and gated by validation + a human**, never
  written straight to the system of record. The rule engine ([[03-validation-rules]])
  and the reviewer ([[06-human-in-the-loop-ux]]) both sit between the agent's
  output and anything treated as fact.

## The `ModelProvider` interface

One interface, two capabilities, both provider-agnostic (ADR-003 — no
LangChain/LangGraph; this is a boundary *we* own, not one borrowed from a
framework):

```python
class ModelProvider(Protocol):
    def extract_lease(self, document_text: str) -> LeaseExtractionResult: ...
    def analyze_photos(self, images: list[ImageRef]) -> PhotoAssessmentResult: ...
```

(`document_text` is plain extracted text, not paginated spans — a real
provider gets long-context input either way, and the stub's own traceability
works by locating a substring within this text directly. Simpler than
threading a separate layout/span structure through the interface for no
current payoff — revisit only if a real provider integration needs
page/bounding-box references the plain text can't carry.)

- `LeaseExtractionResult` = `{ fields: list[ExtractedField], flags: list[FlagCandidate] }`
  where `ExtractedField` matches the [[02-domain-model]] `LeaseField` shape
  (`value`, `confidence`, `source_excerpt`) before persistence.
- `PhotoAssessmentResult` = `{ condition_assessment, detected_contents: list[str],
  damages: list[str], draft_work_order: WorkOrderDraft }`.

### Hard rules

1. **Only the worker calls `ModelProvider`.** The API layer never calls a
   model directly — uploads just enqueue a job (see [[05-pipeline-architecture]]).
   This keeps cost/rate-limit control, retries, and testability in one place,
   and makes the boundary something a code reviewer can actually check for
   (grep for `ModelProvider` usage outside `backend/worker/` → violation).
2. **Every field the agent returns must carry a source reference or an
   explicit "not found."** A field with a value and no `source_excerpt` (and
   `confidence != not_found`) is a bug, not a gap — flag it in review.
3. **Flag-raising is the agent's job, not the rule engine's.** Missing
   fields, contradictions ("start date after end date"), and values that look
   wrong (rent that's 10x the unit's typical range) are things the agent
   notices while reading — the deterministic R1–R7 checks in
   [[03-validation-rules]] run *after*, on the agent's structured output, and
   check different things (business rules, not extraction quality).
4. **The stub implementation is a first-class `ModelProvider`, not a
   shortcut.** It reads the sample lease/photos and returns hand-authored
   structured output with real source spans, so the full pipeline — worker,
   rule engine, UI — is exercised exactly as it would be with a live model.
   Swapping in a real provider is a constructor change, not a rewrite.

## Real-provider requirements (for the README's "API requirements" section)

- **Text model**: long-context (a lease can run several pages), reliable
  structured output or tool-use (function calling) so `LeaseExtractionResult`
  comes back typed, not parsed out of prose.
- **Vision model**: image input alongside structured output — condition
  assessment and content identification both need the model to point at what
  it saw, not just describe it.
- Both are satisfiable by a single provider (e.g. a Claude or GPT-4-class
  model with vision), which is why one `ModelProvider` interface covers both
  capabilities instead of two separate integrations.

## What this layer does *not* cover

- Rule pass/fail logic → [[03-validation-rules]].
- How flags/work orders get reviewed → [[06-human-in-the-loop-ux]].
- Retry/failure handling around the model call → [[05-pipeline-architecture]].
