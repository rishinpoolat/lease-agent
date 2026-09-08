# Spec: Frontend UI polish + real RSC/SSR + code-splitting

Full plan/rationale: see `plan.md` in this folder (mirrors the approved
plan-mode plan). Context layer touched: `docs/context/06-human-in-the-loop-ux.md`
(review-state/badge conventions — preserved, not changed) and
`docs/context/07-decisions.md` ADR-002 (this closes the RSC gap that ADR
already assumed was built).

## Scope

Frontend-only. No backend, schema, rule-engine, or API contract changes.

## Decisions (developer-approved)

- Styling: Tailwind CSS v4 (CSS-first config, `@theme` tokens for the
  existing semantic colors).
- Icons: `@fortawesome/react-fontawesome` + `free-solid-svg-icons`,
  individual tree-shaken icon imports only.
- `app/page.tsx` and `app/units/[unitId]/page.tsx` become real `async`
  Server Components fetching data directly; mutations move into small
  `"use client"` leaf components that call `useRouter().refresh()`.
- `ReviewControl.tsx`'s props/behavior/tests are unchanged — only restyled.
- Add `loading.tsx`/`error.tsx` per route for real Suspense streaming +
  automatic code-splitting.
- No new dependencies beyond Tailwind + Font Awesome; no component library;
  no `next/dynamic` splits invented for their own sake.

## Out of scope

Backend changes, new fields/rules/endpoints, dark mode, auth/RBAC — none of
this task touches those.
