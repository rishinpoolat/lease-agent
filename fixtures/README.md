# Fixtures — synthetic sample data

**Not provided by the property owner.** No real sample lease or photos had arrived
when this was built, so these are authored placeholders used to exercise the
full pipeline end-to-end. Swap them out once the real starter pack lands —
see the repo README.

- `sample_lease.txt` — a synthetic residential lease for Marina Crest
  Residences, Apartment 1204 (Tower B), written to be realistic enough that
  `ModelProvider`'s stub extraction genuinely parses it (regex/keyword
  heuristics over real text), not a canned response keyed to a filename.
- `sample_photos/` — tiny placeholder PNGs. A stub can't see pixels, so
  `analyze_photos` keys off filename hints instead (`*-ac-*`, `*-water-heater-*`,
  `*-wall-damage-*`, …, with a generic fallback for anything else) — see
  `backend/packages/agents/agents/stub.py` and `docs/context/04-agent-boundaries.md`
  for why this is an honest stub rather than hidden magic.
