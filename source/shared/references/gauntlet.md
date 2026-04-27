# The Gauntlet — Full-Spectrum Codebase Audit

Run a full-spectrum, multi-agent audit covering every layer of the application:
architecture, implementation, testing, security, frontend/UX, product alignment,
and blind code review. All rounds run in parallel — contamination is prevented by
instruction, not by timing. Phase 2 begins only after all active rounds complete.

**Trigger:** User-initiated only. Eva does not auto-trigger the Gauntlet.

---

## Execution Rules (read before starting Phase 0)

1. **Parallel execution.** All active rounds in Phase 1 run concurrently. Eva launches every active round as a background agent in a single message. Phase 2 (Combined Register) begins only after all active rounds have written their findings files.
2. **No cross-contamination.** Agents do not read each other's findings files
   during their own review phase. No agent sees what any other agent wrote.
3. **Brain-first.** If brain is available (`brain_available: true` in pipeline-state.md),
   query it before invoking each agent. Inject results as `<brain-context>`.
4. **Upstream-first.** Every agent reads specs, UX docs, and ADRs before reading code.
5. **No hedging.** If something is wrong, state it with file and line. Avoid
   "consider whether" language for clear violations.
6. **Composability thread.** Every agent evaluates composability from their lens.
   This is a first-class concern alongside correctness.
7. **Positive observations required.** Every agent must include at least three
   things done well. A report that only surfaces problems is not balanced.
8. **All rounds run Opus.** No model downgrade regardless of task scope or
   pipeline sizing. The Gauntlet is explicitly high-effort. Omitting the Opus
   model parameter is a Gauntlet configuration error.
9. **Output directory.** All findings files go to `docs/reviews/gauntlet-{YYYY-MM-DD}/`.
   Eva announces the path at the start of Phase 0. The user decides whether
   to commit this directory to version history after reviewing the report.

---

## Severity Definitions (shared across all agents)

| Level    | Meaning |
|----------|---------|
| Critical | Broken in production, data loss risk, active security exploit, or blocking user flow |
| High     | Significant quality gap likely to cause a production incident or user confusion |
| Medium   | Technical debt, spec drift, or missing coverage to address in the next sprint |
| Low      | Best-practice deviation, minor inconsistency, or nice-to-have improvement |

For security findings, Critical = exploitable now without special access.

---

## Findings Table Format (every agent uses this exact schema)

| # | Severity | Layer | Category | Finding | Location | Recommendation |
|---|----------|-------|----------|---------|----------|----------------|

- **Layer:** Backend / API / Frontend / Full-stack / Testing / Infrastructure
- **Category:** Short tag: Auth, Composability, Coverage, Injection, Type-safety, Coupling, etc.
- **Location:** `file:line` preferred; feature/component name when no single file applies
- **Recommendation:** One concrete action sentence

---

## Phase 0 — Eva: Pre-Flight

Before invoking any agent, complete all steps in order. Write all results to
`docs/reviews/gauntlet-{YYYY-MM-DD}/gauntlet-discovery.md`.

### 0a. Create output directory

```
docs/reviews/gauntlet-{YYYY-MM-DD}/
```

If a directory for today already exists (repeated run), append `-2`, `-3`, etc.
Announce the chosen path.

### 0b. Determine scope

Ask the user:

> **Scope:** Full codebase or targeted review?
> 1. **Targeted** — focus on files changed in the last N commits (Eva proposes N based on recent git activity)
> 2. **Full codebase** — all source files

Record the choice as `scope: targeted | full` in the discovery file. If targeted,
run `git log --oneline -{N}` and collect the changed file list. Every subsequent
agent invocation receives `scope` and `changed_files` (if targeted) in their
context block.

### 0c. Opt-in rounds

Ask the user about the two optional rounds:

> **Optional rounds:**
> - **Deps** (Round 8): dependency CVE scan, outdated packages, upgrade risk. Requires `deps_agent_enabled: true` in pipeline-config.json. Adds ~5–10 min.
> - **Agatha** (Round 9): documentation coverage — checks that all significant behavior is documented. Adds ~5–10 min.
>
> Include Deps? (yes / no) Include Agatha? (yes / no)

Record answers. Announce the active round roster before starting Phase 1.

### 0d. Cost gate

Estimate the total cost based on active rounds:

| Rounds | Estimated range |
|--------|----------------|
| 7 rounds (no web routing, no optional) | $3 – $8 |
| 8 rounds (Navigator auto-included) | $3 – $9 |
| 9 rounds (+ Deps or + Agatha) | $4 – $11 |
| 10 rounds (all active) | $5 – $13 |

Present estimate labeled **order-of-magnitude — not billing**. Ask:

> Gauntlet estimate: {N} rounds, Opus throughout.
> Estimated cost: $X – $Y (order-of-magnitude — not billing)
> Proceed? (yes / cancel)

On cancel: stop. Do not write any discovery file.

### 0e. Enumerate documentation artifacts

Search for (adapt paths to what exists in this repo):
- Product/feature specs: `docs/product/`, `docs/specs/`, `specs/`, `product/`
- UX/design docs: `docs/ux/`, `docs/design/`, `design/`
- Architecture Decision Records: `docs/adrs/`, `docs/architecture/`, `adrs/`
- API documentation: `docs/API.md`, `docs/api/`, `openapi.yaml`, `swagger.json`
- Contributing/convention guides: `CONTRIBUTING.md`, `docs/CONVENTIONS.md`, `ARCHITECTURE.md`
- Test strategy docs: `docs/TESTING.md`, `docs/testing/`

List every file found. These are the upstream artifacts every agent must read
before touching code.

### 0f. Map application structure

Fan out 4 scout subagents in parallel to collect raw evidence cheaply.
Each scout returns facts only — no design opinions.

| Scout | What it collects |
|-------|-----------------|
| **Structure** | Backend entry points, router files, service/domain layer dirs, data layer, API layer |
| **Frontend** | Entry points, routing config, component dirs, state management, API client |
| **Tests** | Test roots, config files, test type distribution (unit/integration/e2e count) |
| **Deps** | Dependency manifests, CI/CD config, .env.example, docker files |

Collect scout results. Write structured map to discovery file. This map is
passed to every agent as part of their invocation context.

### 0g. Query the brain (if available)

Call `agent_search` with queries:
1. `"architectural decisions past incidents technical debt"`
2. `"recurring bugs rejected approaches security vulnerabilities"`
3. `"composability coupling layer violations"`

Summarize results. Inject into every subsequent agent invocation as `<brain-context>`.

### 0h. Write discovery summary

`docs/reviews/gauntlet-{YYYY-MM-DD}/gauntlet-discovery.md` — structured with:
- Scope setting and changed files list (if targeted)
- Active round roster
- Complete artifact file list with one-line descriptions
- Application structure map (top-level only)
- Brain context summary (or "Brain unavailable")

This file is passed to every agent as part of their invocation.

---

## Phase 1 — Parallel Agent Reviews

Launch all active agents simultaneously as background subagents in a single
message. Each agent's output goes to:


Eva waits for all completion notifications before starting Phase 2.`docs/reviews/gauntlet-{YYYY-MM-DD}/gauntlet-findings-{agent}.md`

---

### Round 1 — Sarah: Architectural Integrity & Composability

**Model:** Opus

**Mandate:** Assess whether the system's architectural decisions are faithfully
implemented and whether the design supports composition, evolution, and change
without cascading modification.

**Review lens:**

**ADR alignment**
- For each ADR/architecture doc: is the decision reflected in the code, or has
  it drifted? List each decision, its intended behavior, and actual behavior.
- Are there implicit architectural decisions living only in code, with no ADR?
  These are institutional debt.

**Layer discipline**
- Is business logic confined to the service/domain layer? Are routes and
  controllers thin (validate input, call service, return result — nothing more)?
- Is the persistence layer abstracted (does the service layer depend on
  repository interfaces, not ORM internals)?
- Is there any logic in view/template/component files that belongs in a service?
- Are there cross-layer leaks in either direction (UI logic in backend, DB
  queries in routes)?

**Composability — the composability question for every module/service/component:**
  "Can this be used in a new context without modifying its internals?"
- Do services compose by dependency injection (not inheritance or global state)?
- Are there God objects/services that do too many things and cannot be decomposed?
- Are interfaces/contracts defined before implementations (stable APIs)?
- Does the system follow the open/closed principle? Where is this violated?
- Are there tight point-to-point integrations that should be event-driven or
  interface-abstracted?
- Identify modules that cannot be replaced without touching their callers.

**API contract design**
- Are API response shapes minimal and stable (no leaking internal model fields)?
- Are request/response contracts versioned or evolution-safe?
- Is there a consistent pattern for pagination, filtering, error envelopes, and
  status codes — or does each endpoint invent its own?

**Async discipline**
- Is async/await applied consistently? Are there sync calls blocking async
  contexts? Unhandled promise rejections?
- Are race conditions architecturally possible (shared mutable state, no
  optimistic locking where needed)?

**Pattern consistency**
- Do later-built features follow the same patterns as earlier features?
- Are there multiple generations of the same abstraction where one should exist?

**Missing architecture**
- Where is the system likely to grow next? Is there a clean extension point, or
  will growth require broad refactoring?

**Output file:** `docs/reviews/gauntlet-{YYYY-MM-DD}/gauntlet-findings-sarah.md`

```
# Sarah — Architectural Integrity & Composability

## Summary
[3-4 sentence executive assessment]

## ADR Alignment Matrix
| ADR | Decision | Code Status | Notes |
|-----|----------|-------------|-------|
| ADR-NNN | ... | Aligned / Partial / Drifted | ... |

## Composability Scorecard
| Module/Service/Component | Composable? | Blocker | Recommendation |

## Findings
| # | Severity | Layer | Category | Finding | Location | Recommendation |

## Positive Observations
[Minimum 3 things working well architecturally]

## Missing ADRs (decisions made in code with no documentation)
[List]
```

---

### Round 2 — Colby: Implementation Quality & Technical Debt

**Model:** Opus

**Mandate:** Review code quality, implementation correctness, and accumulated
technical debt across every layer. Look for things that pass tests but are
wrong, fragile, or will break at scale.

**Review lens:**

**Composability at the code level**
- Are functions and methods single-purpose? Can they be reused without
  modification or re-testing?
- Is logic parameterized rather than hardwiring dependencies internally?
- Are there large functions (>50 lines) embedding multiple distinct concerns?
- Are utility functions genuinely general, or secretly domain-specific with a
  generic name?

**Code duplication**
- Identify logic blocks copied across files that should be a shared utility.
  Same pattern appearing 3+ times is a flag.
- Are there multiple implementations of the same concept?

**Error handling discipline**
- Is error handling present at system boundaries and absent inside well-controlled
  internals? Inverting this pattern is a defect.
- Are caught errors re-thrown with context, or swallowed silently?
- Are user-visible error messages helpful, or do they expose internal details?

**Type safety**
- Are there `any` casts, type assertions, or non-null assertion operators that
  mask real uncertainty?
- Are API response shapes explicitly typed end-to-end?

**Configuration discipline**
- Is all environment-specific config sourced from env vars / config files?
- Are there hardcoded values (URLs, timeouts, limits, credentials) that belong
  in config?

**Dead code & consistency**
- Unused exports, unreachable branches, commented-out blocks, TODO/FIXME markers
- Are similar CRUD operations implemented consistently?

**Query efficiency**
- N+1 query patterns
- Fetching more data than needed
- Missing pagination on endpoints that return potentially large lists

**Async correctness**
- Unresolved promises, fire-and-forget without error handling
- Race conditions from concurrent async operations sharing state
- Blocking calls inside async paths

**Boundary validation**
- Is input validated at every entry point?

**Output file:** `docs/reviews/gauntlet-{YYYY-MM-DD}/gauntlet-findings-colby.md`

```
# Colby — Implementation Quality & Technical Debt

## Summary

## Findings
| # | Severity | Layer | Category | Finding | Location | Recommendation |

## Positive Observations
[Minimum 3 things implemented well]
```

---

### Round 3 — Poirot: Testing Strategy & Coverage

**Model:** Opus

**Mandate:** Audit the testing strategy for completeness, confidence, and
resilience. Identify what the test suite would miss in production, and where
passing tests provide false assurance.

**Review lens:**

**Coverage topology**
- Map critical business flows to test coverage: fully tested / partially tested / untested.
- Which high-risk paths (auth, payment, data mutation, permission checks) have
  no integration test?
- Are there files with 0% test coverage that are not trivially safe to leave uncovered?

**Test type balance**
- Is there an appropriate pyramid: many unit tests, fewer integration tests,
  minimal e2e?
- Is the pyramid inverted (mostly mocks and unit tests with no integration layer)?

**Mock depth**
- Are mocks applied at the right boundary (external HTTP, file system, clock)?
- Are integration tests hitting a real database/cache or mocking the DB driver?
- Are there tests that pass with mock data that would fail with real data shapes?

**Happy-path bias**
- For each critical feature's test file: what percentage of tests exercise
  error paths, edge cases, invalid inputs, or race conditions?

**Test quality**
- Do tests assert on behavior or on implementation details?
- If the implementation changes but behavior stays the same, will tests break?
  If yes, they're testing implementation, not behavior.

**Flakiness risk**
- Time-dependent assertions (sleep, fixed timestamps, Date.now())
- Unordered collection comparisons without sorting
- Tests that depend on execution order

**Spec-to-test traceability**
- For each acceptance criterion in the product specs, is there a test that
  fails when that criterion is violated?

**Contract testing**
- Are request/response shapes validated by any test?
- Are error envelopes tested?

**Composability of tests**
- Are test fixtures/factories composable and reusable?

**Output file:** `docs/reviews/gauntlet-{YYYY-MM-DD}/gauntlet-findings-qa.md`

```
# Poirot — Testing Strategy & Coverage

## Summary

## Coverage Map
| Feature / Business Flow | Coverage Level | Highest-Risk Gap |
|------------------------|----------------|-----------------|

## Spec-to-Test Traceability
| Spec | Acceptance Criterion | Test exists? | Test file |

## Findings
| # | Severity | Layer | Category | Finding | Location | Recommendation |

## Positive Observations
[Minimum 3 things the test suite does well]
```

---

### Round 4 — Sentinel: Security Audit

**Model:** Opus

**Mandate:** Identify security vulnerabilities, authorization gaps, and data
exposure risks across the full stack. Use the OWASP Top 10 as a minimum
baseline, then go deeper on authentication, secrets, and data boundaries.

**Review lens:**

**Broken access control**
- Is authorization checked on every protected endpoint?
- Are role checks applied at the service layer (not just the route layer)?
- Are object-level permissions verified?

**Injection**
- Are all database queries parameterized / using prepared statements?
- Are shell commands, file paths, or template expressions constructed from
  user-supplied input?

**Cryptographic failures**
- Is sensitive data encrypted at rest?
- Are weak algorithms present: MD5, SHA1, ECB mode, DES, RC4?
- Are passwords hashed with a strong adaptive algorithm?
- Are JWTs validated correctly?

**Authentication failures**
- Are session tokens invalidated on logout?
- Are there brute-force protections on login, password reset, and OTP endpoints?
- Are OAuth flows implemented correctly?

**Security misconfiguration**
- Are stack traces returned to the client?
- Is CORS configured restrictively?
- Are security headers present (CSP, X-Frame-Options, HSTS, etc.)?
- Are CSRF protections in place?

**Sensitive data exposure**
- Is PII appearing in log statements, error messages, or analytics events?
- Are API keys, tokens, or passwords appearing in logs on error?

**Composability of security controls**
- Are security middleware/guards reusable and consistently applied?
- Can a new endpoint be added without security being applied (opt-in vs opt-out)?

**Rate limiting & DoS surface**
- Are computationally expensive endpoints rate-limited?
- Are authentication endpoints rate-limited?

**Supply chain**
- Are dependency lockfiles committed and pinned?

**Output file:** `docs/reviews/gauntlet-{YYYY-MM-DD}/gauntlet-findings-sentinel.md`

```
# Sentinel — Security Audit

## Summary

## OWASP Coverage Assessment
| Category | Status | Notes |
|----------|--------|-------|

## Findings
| # | Severity | Layer | Category | Finding | Location | Recommendation |

## Positive Observations
[Minimum 3 security controls working well]
```

---

### Round 5 — Sable: Frontend & UX Quality

**Model:** Opus

**Mandate:** Review the frontend implementation for UX spec fidelity, component
composability, accessibility, state resilience, and type safety at the
frontend boundary.

**Note:** If the project has no frontend, replace the full round with a
"Frontend: N/A" section in the combined register. Eva announces this
substitution in Phase 0.

**Review lens:**

**UX spec alignment**
- For each screen, flow, or interaction in the UX docs: is the implementation
  faithful? What is missing, changed without justification, or added without a spec?
- If no UX docs exist, Sable reviews component patterns and accessibility without
  a spec baseline.

**Component composability**
- Does each component do one thing?
- Are props interfaces minimal and stable?
- Is composition used over configuration?
- Is prop drilling more than 2 levels deep?
- Are there duplicate components implementing the same UI pattern?

**State completeness**
- For every data-fetching component: are loading, error, empty, and populated
  states all explicitly handled?
- Are optimistic updates rolled back on failure?

**Accessibility**
- Are interactive elements keyboard-navigable and focus-visible?
- Are ARIA roles and labels present on interactive elements that lack visible
  text labels?
- Are color contrast ratios sufficient?
- Are form fields associated with labels?

**Error boundaries & resilience**
- Are component-level error boundaries in place?
- Are network error states handled at each data-fetching boundary?

**Type safety at the frontend boundary**
- Are API response types explicitly defined?
- Do types weaken anywhere between the API call and the rendered output?

**Performance signals**
- Are large lists virtualized?
- Are heavy components lazy-loaded?
- Are there obvious unnecessary re-renders?

**Output file:** `docs/reviews/gauntlet-{YYYY-MM-DD}/gauntlet-findings-sable.md`

```
# Sable — Frontend & UX Quality

## Summary

## UX Spec Alignment Matrix
| Screen / Flow | Spec Status | Implementation Status | Gap |

## Findings
| # | Severity | Layer | Category | Finding | Location | Recommendation |

## Positive Observations
[Minimum 3 things done well in the frontend]
```

---


### Round 6 — Navigator: Route Integrity & Access Control

**Model:** Opus

**Condition:** Runs automatically when Eva detects a web frontend with routing
during Phase 0 (router files, nav components, route guard patterns). If no
web routing is detected, replace the full round with a "Navigator: N/A —
no web routing detected" row in the combined register.

**Mandate:** Walk every navigable route in the application. For each route,
verify the link exists, the destination loads, and the auth/access rules
match the spec and implementation. Surface dead links, orphan routes, and
access-rule drift that no other agent is looking for.

**Critical constraint:** Navigator reads route definitions, nav components,
auth middleware, and specs. It does NOT run a live server or make HTTP
requests. All verification is static: tracing route definitions to their
handlers, nav links to their destinations, and auth guards to their policies.

**Review lens:**

**Link integrity**
- For every navigation link (sidebar, header, tabs, breadcrumbs, programmatic
  `navigate()` / `router.push()` calls): does the target route exist?
- Are there any 404-producing links in the current codebase?
- Are there any routes defined but never linked from navigation (orphan routes)?

**Page load correctness**
- For each route, does the component/page it renders actually exist?
- Are there lazy-loaded routes whose chunk is not present in the build output?
- Are there route aliases or redirects that point to missing destinations?

**Auth and access rules**
- For each protected route: is the auth guard actually applied (not just
  documented)?
- Can an unauthenticated user navigate to a page that requires login?
- Are there routes where the guard is applied in the route definition but
  bypassed by a component-level navigation shortcut?
- Does the spec (product docs, UX docs) describe any access-level
  requirements (admin-only, owner-only, logged-in-only) for a route? Does
  the implementation match?

**Consistency**
- Are auth guards applied consistently — one pattern throughout, or a mix of
  route-level guards, component-level checks, and server-side redirects?
- Are error states (unauthorized, forbidden, not-found) handled at each
  protected route?

**Output file:** `docs/reviews/gauntlet-{YYYY-MM-DD}/gauntlet-findings-navigator.md`

```
# Navigator — Route Integrity & Access Control

## Summary

## Route Matrix
| Route / Path | Linked From | Handler Exists? | Auth Guard | Spec Says | Drift? |
|---|---|---|---|---|---|

## Findings
| # | Severity | Layer | Category | Finding | Location | Recommendation |

## Orphan Routes (defined, never linked)
[List]

## Dead Links (linked, no matching route)
[List]

## Positive Observations
[Minimum 3 things — routing structure, auth consistency, or error handling
done well]
```

---
### Round 7 — Robert: Product & Spec Alignment

**Model:** Opus

**Mandate:** Assess whether the implemented product matches its specifications.
Identify missing criteria, spec drift, orphaned features, and product-quality
gaps a real user would encounter. Also evaluate composability through a product
lens: are user flows self-contained and reusable across different entry points?

**Review lens:**

**Acceptance criteria coverage**
- For each acceptance criterion across all feature specs: is it fully
  implemented, partially implemented, or missing?

**Spec drift**
- Are there implemented behaviors that contradict a spec?
- Are there API responses, UI states, or error messages that differ from what
  the spec describes?

**Orphaned code**
- Are there API endpoints, UI routes, or significant logic blocks with no
  corresponding spec?

**Edge case handling**
- Does each spec define behavior for: empty state, first-time user, limit
  condition, concurrent operation, and failure mode?
- For each defined edge case: is it implemented?

**API/UI contract**
- Does the API return exactly what the frontend needs?
- Are the API field names consistent between the spec, the backend, and the
  frontend?

**User-visible quality**
- Are user-facing error messages accurate, specific, and actionable?
- Are empty states informative?

**Composability (product lens)**
- Can user flows be entered from multiple access points (deep link, navigation,
  onboarding) without breaking?
- Is shared state managed in a way that does not lock a feature to a single
  entry sequence?

**Missing specs**
- Are there significant areas of the codebase where behavior is implemented
  but no spec was ever written?

**Output file:** `docs/reviews/gauntlet-{YYYY-MM-DD}/gauntlet-findings-robert.md`

```
# Robert — Product & Spec Alignment

## Summary

## Acceptance Criteria Coverage Matrix
| Feature | Total Criteria | Implemented | Partial | Missing |

## Findings
| # | Severity | Layer | Category | Finding | Location | Recommendation |

## Positive Observations
[Minimum 3 areas where spec and implementation are in excellent alignment]

## Unspecified Features (code exists, no spec)
[List]
```

---

### Round 8 — Poirot: Blind Code Review

**Model:** Opus

**Mandate:** Review the codebase without any spec, ADR, UX doc, or context.
Evaluate purely on observable properties: is this code correct, safe, and
readable on its own terms? What would a reviewer seeing it for the first time
find suspicious, fragile, or wrong?

**Critical constraint:** Poirot reads code only. No spec files, no ADR files,
no UX docs, no round-table discovery file, no other agents' findings files.
Passing Poirot anything beyond the source code is a Gauntlet configuration error.

**Review lens:**

**Code smell inventory**
- Long functions (>50 lines), deep nesting (>3 levels), too many parameters (>5)
- Magic numbers and strings with no explanation
- Functions that do more than their name suggests
- Comments that describe what the code does (not why) — a sign the code is
  not self-explanatory

**Defensive programming gaps**
- Assuming a value is not null/undefined when there is no proof
- Assuming a list is non-empty
- Assuming an external call always succeeds
- Assuming a type cast is safe

**Naming and consistency**
- Names that are misleading, abbreviated beyond recognition, or inconsistent
  with neighboring names
- Verbs used as nouns, nouns used as functions
- Similar concepts with dissimilar names across files

**Structural integrity**
- Functions that are called but never defined (dead symbols pointing to nothing)
- Circular imports or dependency cycles
- Files that import from too many places (high coupling)

**Systemic patterns** — when the same defect class recurs in 3+ places, Poirot
reports it as a single finding with `scope: systemic` and lists all locations.
This is not a deduplication shortcut — it identifies a pattern the team should
address as a class, not as individual instances.

**Positive signals**
- Code that is so clear it needs no comments
- Error handling that is both thorough and non-intrusive
- Abstractions that genuinely simplify their callers

**Output file:** `docs/reviews/gauntlet-{YYYY-MM-DD}/gauntlet-findings-poirot.md`

```
# Poirot — Blind Code Review

## Summary

## Findings
| # | Severity | Layer | Category | Finding | Location | Recommendation | Scope |

(Scope column: "local" or "systemic". Systemic findings list all locations in the Finding cell.)

## Positive Observations
[Minimum 3 things observed without any context clue that are clearly well done]
```

---

### Round 9 — Deps: Dependency Health (optional)

**Model:** Sonnet (Deps base model; universal classifier applies)

**Condition:** Only runs if user opted in during Phase 0 and
`deps_agent_enabled: true` in pipeline-config.json.

**Mandate:** Scan all dependency manifests for CVEs, outdated packages, and
upgrade risk. Predict breakage by cross-referencing usage patterns against
changelogs.

**Output file:** `docs/reviews/gauntlet-{YYYY-MM-DD}/gauntlet-findings-deps.md`

```
# Deps — Dependency Health

## Summary

## Risk-Grouped Report
| Package | Current | Latest | CVE | Breakage Risk | Recommendation |

## Positive Observations
[Dependencies managed well — pinned, audited, or recently upgraded]
```

---

### Round 10 — Agatha: Documentation Coverage (optional)

**Model:** Sonnet (Agatha conceptual doc model; see pipeline-models.md)

**Condition:** Only runs if user opted in during Phase 0.

**Mandate:** Assess whether the codebase's behavior is documented at the level
a new contributor would need to work confidently. Identify behaviors, systems,
and decisions that exist only in code with no prose explanation.

**Review lens:**
- Are all public API surfaces documented?
- Are complex algorithms or non-obvious implementation choices explained?
- Are operational procedures (setup, deployment, configuration) documented?
- Are ADRs present for major architectural decisions?
- Are there areas where the code is the only source of truth for behavior
  that changes frequently?

**Output file:** `docs/reviews/gauntlet-{YYYY-MM-DD}/gauntlet-findings-agatha.md`

```
# Agatha — Documentation Coverage

## Summary

## Coverage Assessment
| Area | Documented? | Gap | Priority |
|------|-------------|-----|----------|

## Findings
| # | Severity | Layer | Category | Finding | Location | Recommendation |

## Positive Observations
[Minimum 3 areas with documentation that is genuinely useful]
```

---

## Phase 2 — Eva: Combined Findings Register

After all active agents complete, Eva reads all findings files and produces
the combined register. No agent is invoked in this phase — this is Eva's work.

### Deduplication rules

- If two or more agents flag the same issue (same root cause at the same
  location, or the same systemic pattern across the same layer), merge into
  one row.
- Use the highest severity assigned by any agent for the merged row.
- List all agents that independently flagged it in the `Agents` column.
  Multi-agent agreement is a confidence signal — surface it prominently.
- Poirot systemic findings (`scope: systemic`) merge as a single row even if
  they span many locations. The merged row carries the `scope: systemic`
  annotation and lists all locations in the Finding cell.

### Sort order

Critical → High → Medium → Low.
Within each severity: most agents agreeing first (descending agreement count).

### Output file: `docs/reviews/gauntlet-{YYYY-MM-DD}/gauntlet-combined.md`

```markdown
# The Gauntlet — Combined Findings Register
Generated: {date}
Scope: {full-codebase | targeted: last N commits ({commit-range})}
Rounds: {active round list}

---

## Executive Summary
[5-7 sentences. Overall health signal. Most critical themes. Patterns of agreement.
What the team is doing well at a systemic level. Top recommended action.]

---

## Multi-Agent Findings (agreed by 2+ agents)

*These carry the highest confidence — multiple independent specialists converged
on the same signal.*

| # | Severity | Layer | Category | Finding | Location | Recommendation | Agents |
|---|----------|-------|----------|---------|----------|----------------|--------|

---

## Single-Agent Findings

*Flagged by one specialist. Still actionable — single-agent findings often
reflect domain-specific expertise the others were not looking for.*

| # | Severity | Layer | Category | Finding | Location | Recommendation | Agent |
|---|----------|-------|----------|---------|----------|----------------|-------|

---

## Positive Observations (Consensus)

*Patterns multiple agents independently praised. Preserve and extend these as
the system grows.*

| Observation | Agents |
|-------------|--------|

---

## Composability Report

A dedicated summary of composability findings across all agents.

| Layer | Component / Module | Composable? | Primary Blocker | Agents Who Flagged |
|-------|-------------------|-------------|-----------------|-------------------|

---

## Recommended Priority Order

Top 10 actions ordered by impact × urgency. Each action traces to its source
findings.

| Priority | Action | Severity | Source Findings | Rationale |
|----------|--------|----------|-----------------|-----------|

---

## Coverage Gaps Summary

Areas where the audit found insufficient evidence to assess (no spec,
no tests, no ADR, no UI implementation).

| Area | Gap Type | Recommended Next Step |
|------|----------|-----------------------|
```

---

## Phase 3 — Eva: Handoff

After writing the combined register, Eva:

1. Announces all files produced (one line each with full path)
2. Produces a **qualitative health summary** (see format below)
3. States the output directory and whether to `git add` it to commit the history
4. **Stops.** No routing to Colby. No automatic pipeline. No fix suggestions.

The Gauntlet is a read-and-review artifact. The user decides what to act on.
If the user wants to act on findings, they start a new pipeline.

**Handoff format:**

```
The Gauntlet is complete.

Files produced:
  docs/reviews/gauntlet-{YYYY-MM-DD}/gauntlet-discovery.md
  docs/reviews/gauntlet-{YYYY-MM-DD}/gauntlet-findings-{agent}.md  (one per round)
  docs/reviews/gauntlet-{YYYY-MM-DD}/gauntlet-combined.md

---
Codebase Health Summary
---

**Broken today** -- behavior currently failing or producing wrong results in
normal usage (user is hitting this now, or data is being lost now):
  - [finding title]: one sentence on what is actually broken
  (if none: "Nothing confirmed broken in normal usage.")

**Silently failing** -- things that appear to work but do not. No error
visible to the user, but output is wrong, incomplete, or discarded:
  - [finding title]: one sentence on what looks fine but is not
  (if none: "No silent failures identified.")

**Security concerns** -- exploitable now or a clear path to exploitation
without special access:
  - [finding title]: one sentence on the exposure and who can reach it
  (if none: "No active security concerns identified.")

**Will hurt soon** -- not broken today, but will cause a production incident,
data loss, or a blocked sprint within the next 1-3 weeks if not addressed:
  - [finding title]: one sentence on when/how this becomes a problem
  (if none: "No near-term crystallization risk identified.")

**Healthy debt** -- real problems, but not urgent. The codebase works despite
these. Worth a cleanup sprint, not an emergency fix:
  - [brief label]: one sentence (3-5 items max)

**What is genuinely working well** (2-3 sentences):
  [Honest positive signal -- not a consolation prize. What would a new
  contributor notice first as genuinely good about this codebase?]

---
Top 3 actions (from gauntlet-combined.md Priority Order):
  1. [action]
  2. [action]
  3. [action]
---
```

**Rules for the health summary:**

- **Broken today** and **Silently failing** are the only categories that
  require immediate action. If both are empty, say so explicitly -- that is
  good news worth stating.
- Never put a finding in **Broken today** unless confirmed to fail in the
  normal workflow, not just in an edge case or test scenario.
- **Severity levels are not categories.** A Critical finding may belong in
  "healthy debt" if it only manifests rarely. A Medium finding may belong in
  "broken today" if it affects the default path. Map to operational impact,
  not severity label.
- The summary must be readable in 60 seconds. If a category has more than
  5 bullets, consolidate -- the combined register has the full list.
- **Will hurt soon** requires a known trigger: "the next time X happens,
  this breaks." Findings with no known trigger belong in healthy debt.

To commit: git add docs/reviews/gauntlet-{YYYY-MM-DD}/ and include in your next commit.
To act on findings: start a new pipeline with the relevant findings as input.

---

## Adapting to Any Project

When dropping this reference into a project that differs from the expected
structure, Eva adapts at discovery time (Phase 0h) and announces all adaptations
before starting Phase 1:

- **No ADRs:** Sarah's ADR alignment matrix is replaced with an "Undocumented
  Decisions" section identifying architectural choices with no written record.
- **No product specs:** Robert's acceptance criteria matrix is replaced with a
  "Reverse-Engineered Requirements" section inferred from code behavior.
- **Backend-only project:** Sable's round is skipped; announce "Round 5 (Sable):
  N/A — no frontend detected." Include a placeholder row in the combined register.
- **Frontend-only project:** Scope Sarah and Colby to frontend architecture.
- **No UX docs:** Sable reviews component patterns and accessibility without
  a spec baseline.
- **Targeted scope:** All agents receive `scope: targeted` and `changed_files`
  in their context. Agents focus findings on the changed files but may flag
  systemic patterns they observe incidentally.
