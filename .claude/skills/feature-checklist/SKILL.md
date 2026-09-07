---
name: feature-checklist
description: What to consider before/while planning a feature — checking for existing functionality, running the context-layer cascade, deciding if a spec is warranted, scoping, and test coverage needs. Use this whenever a feature is requested and plan mode is being entered.
---

# Before Building a Feature

Considerations to run through before/while proposing a plan:

- Check `CODEBASE_MAP.md` first — does similar functionality already exist?
  Don't duplicate.
- Run the context-layer cascade (`.claude/rules/context-layers.md`) — this
  usually answers scope, data shape, and UX conventions before you'd have to
  guess. See `docs/context/01-requirements.md` in particular for whether the
  request is even in scope.
- Does this need a spec? (multi-file, ambiguous, touches the agent/rule/queue
  boundary → yes. Small/obvious → plan mode only, no spec doc needed.)
- What's explicitly out of scope for this pass?
- Which existing tests might this affect, and will this feature need new
  unit tests, an integration test, or both?

## Asking concrete clarifying questions, not generic ones

"Surface open questions instead of guessing" means asking the *specific*
question the feature actually needs answered — not a vague "any
preferences?" Match the question to the domain:

Example — request: "add support for a second document type (addenda)"
Good clarifying questions:
- Does an addendum modify existing `LeaseField` rows (supersede) or add new
  ones alongside the original lease's fields?
- Should `RuleEvaluation` re-run against the merged (lease + addendum) state,
  or does the addendum get its own evaluation?
- Same `lease.extraction` queue, or a new job type?

Bad: a single generic "what are your requirements for addenda?" — this
pushes the thinking back onto the developer instead of narrowing down the
real decision points the way a colleague familiar with the domain would.

Ask the smallest set of concrete questions that actually changes the plan
depending on the answer — not every conceivable question, just the ones
where different answers lead to a different implementation.

This is a standing rule for the rest of the current task — if more features
get requested later in the same session, this checklist applies again each
time.
