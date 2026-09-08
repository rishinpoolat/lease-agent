# Plan: Frontend UI polish + real RSC/SSR + code-splitting

Spec: `spec.md` in this folder. Full design rationale copied from the
approved plan-mode plan (developer approved 2026-09-08).

## To Do
- (none)

## In Progress
- (none)

## Completed
- [x] Tailwind CSS v4 (`postcss.config.mjs`, `@theme` tokens for
  pass/fail/warn/muted in `globals.css`) + Font Awesome
  (`react-fontawesome` + `free-solid-svg-icons`, individual tree-shaken
  icon imports).
- [x] `app/page.tsx` and `app/units/[unitId]/page.tsx` converted to real
  `async` Server Components (direct `await api.*()` during render).
- [x] Client islands: `ReviewField`, `ReviewFlag`, `ReviewWorkOrder`,
  `AcceptUnitMatchCard` — each owns its own mutation + `router.refresh()`.
  `ReviewControl` itself unchanged (props/behavior/tests untouched).
- [x] `StatusBadge` shared component (review-status + rule-verdict
  families, distinct styling per docs/context/06).
- [x] `app/{loading,error}.tsx`, `app/units/[unitId]/{loading,error}.tsx`
  — real per-route Suspense/error boundaries.
- [x] `next/font/google` (Inter) in `layout.tsx`; restyled upload pages
  and `ReviewControl` with Tailwind, no behavior change.
- [x] Bug found mid-implementation and fixed: server-side fetches (RSC)
  run inside the `web` container, where `localhost:8000` doesn't reach
  the `api` container — `lib/api.ts` now picks `API_URL` (server) vs
  `NEXT_PUBLIC_API_URL` (browser) based on `typeof window`;
  `docker-compose.yml`'s `web` service sets `API_URL: http://api:8000`.
- [x] Verified: `npm test` (6/6 unmodified), `npm run lint` (clean),
  `npm run build` (route table confirms `/` and `/units/[unitId]` are
  dynamic/SSR, upload pages static), live curl against
  `docker compose`'s `web` container confirms populated HTML on first
  response (real SSR, not a client-only shell) and FA icon SVGs +
  Tailwind classes present in the markup.
- [x] `CODEBASE_MAP.md`'s `frontend/` section updated to describe the
  Server-Component/client-island split.
- [x] Mid-implementation, developer asked for shadcn/ui on top of the
  Tailwind/FA base (screenshot feedback: buttons looked flat/undifferentiated,
  wanted darker blue/green). Ran `shadcn@latest init` + added
  `button`/`badge`/`card`/`input`; extended the generated `Button` with a
  `success` variant (`bg-pass`) for Accept, `destructive` for Reject,
  `outline` for Edit/Cancel. Removed `lucide-react` (unused — icons stay
  Font Awesome per the original decision) and, later, `tw-animate-css`
  (its "style" export condition wasn't resolvable by Turbopack dev inside
  the Docker container — confirmed working in a host `next build` but not
  container `next dev`; dropped since nothing we use depends on it, rather
  than fighting the resolver). Consolidated shadcn's generated design
  tokens with the project's existing `pass`/`fail`/`warn`/`muted` badge
  tokens in one `@theme` block; set `--primary`/`--ring` to a darker blue
  (`#1e40af`) and `--color-pass` to a darker green (`#15803d`) per
  developer feedback on a live screenshot.
- [x] Follow-up developer feedback (second screenshot): reverted the
  `next/font/google` Inter addition back to the plain system font stack
  ("keep the normal font"), and fixed `ReviewControl`'s Accept/Reject/Edit
  row wrapping onto two lines by switching its flex container from
  `flex-wrap` to `flex-nowrap` + `whitespace-nowrap` and giving the
  Review table column a `w-56` floor.
- [x] Code-reviewer's one real finding (FontAwesome SSR flash-of-unstyled-
  icons — `config.autoAddCss = false` + explicit core CSS import missing)
  fixed via new `lib/fontawesome.ts`, imported once in `app/layout.tsx`.
  Nits also fixed: hoisted duplicated `displayValue` to `lib/format.ts`,
  added tests for the four new client-wrapper components + `StatusBadge`
  (16 new tests), corrected `CODEBASE_MAP.md`'s overstated claim about
  badge-family color distinctness.
- [x] Verified against the live `docker compose` stack (not just `npm run
  build` on the host): fixed a real bug the RSC conversion exposed —
  server-side fetches run inside the `web` container, where
  `localhost:8000` doesn't reach the `api` container. `lib/api.ts` now
  branches on `typeof window` (`API_URL` server-side vs
  `NEXT_PUBLIC_API_URL` browser-side); `docker-compose.yml`'s `web`
  service sets `API_URL: http://api:8000`. Confirmed via curl against the
  container that the full page (38 icons, all field/rule/flag rows) is
  genuinely present in the initial server-streamed response, not a
  client-only shell.
- [x] Per the developer's separate request, removed all `.claude/`
  references from `CODEBASE_MAP.md` (the file now only points at
  `CLAUDE.md`, not the Claude Code tooling directory).
