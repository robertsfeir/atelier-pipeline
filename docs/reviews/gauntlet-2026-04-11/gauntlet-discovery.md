# Gauntlet Discovery — 2026-04-11

Generated: 2026-04-11
Output directory: `docs/reviews/gauntlet-2026-04-11/`

---

## Scope

**Setting:** Full codebase
**Changed files list:** N/A (full codebase scope)

---

## Active Round Roster

| Round | Agent | Model | Status |
|-------|-------|-------|--------|
| 1 | Cal — Architectural Integrity & Composability | Opus | Pending |
| 2 | Colby — Implementation Quality & Technical Debt | Opus | Pending |
| 3 | Roz — Testing Strategy & Coverage | Opus | Pending |
| 4 | Sentinel — Security Audit | Opus | Pending |
| 5 | Sable — Frontend & UX Quality | Opus | Pending |
| 6 | Robert — Product & Spec Alignment | Opus | Pending |
| 7 | Poirot — Blind Code Review | Opus | Pending |
| 8 | Deps — Dependency Health | Sonnet | **Blocked: `deps_agent_enabled: false` in pipeline-config.json** |
| 9 | Agatha — Documentation Coverage | Sonnet | Pending |

> **Deps note:** User opted in to Round 8 but `deps_agent_enabled: false`. Round 8 will run if user sets flag to `true`. Rounds 1–7, 9 proceed.

---

## Upstream Artifacts (every agent reads before code)

### Architecture Decision Records — 33 ADRs across docs/architecture/ and docs/brain/

Most recently relevant:
- ADR-0033 (839L) — Hook enforcement audit fixes (most recent, just completed)
- ADR-0032 (551L) — Pipeline state session isolation
- ADR-0031 (330L) — Permission audit trail
- ADR-0030 (257L) — Token exposure probe
- ADR-0029 (357L) — Token budget estimate gate
- ADR-0028 (261L) — Stop reason taxonomy
- ADR-0027 (367L) — Brain hydration scout fanout
- ADR-0026 (745L) — Beads provenance records
- ADR-0025 (424L) — Mechanical telemetry extraction
- ADR-0024 (548L) — Mechanical brain writes
- ADR-0023 (719L) — Agent spec reduction (~57%)
- ADR-0022 (1291L) — Wave 3 native enforcement redesign
- ADR-0021-active (742L) — Brain wiring
- ADR-0020-active (614L) — Wave 2 hook modernization
- ADR-0005 (1087L) — XML prompt structure (foundational)
- ADR-0001 (1058L) — Atelier Brain architecture (in docs/brain/)
- Plus ADR-0002 through ADR-0019 (various)

### Product Specs — 9 files in docs/product/

agent-telemetry.md (222L), brain-hardening.md (124L), ci-watch.md (212L), cursor-port.md (191L),
darwin.md (270L), dashboard-integration.md (212L), deps-agent.md (194L),
mechanical-brain-writes.md (203L), team-collaboration-enhancements.md (108L)

### UX/Design Docs

**None.** `docs/ux/` does not exist.
Partial UX coverage: `docs/brain/atelier-brain-settings-ux.md` (285L).

### User Guide / Technical Reference

- docs/guide/user-guide.md (1528L)
- docs/guide/technical-reference.md (2528L)

### Contributing / Convention Guides

- README.md (415L), CONTRIBUTING.md (94L), AGENTS.md (49L), CHANGELOG.md (459L)

---

## Application Structure Map

### Repository Layout

```
atelier-pipeline/
├── source/                    # Template source — triple-target
│   ├── shared/                # Platform-agnostic: agents(15), commands(11), hooks(1), rules(4), references(14), pipeline(6)
│   ├── claude/                # Claude overlays: agents(15), commands(11), hooks(23), rules(2)
│   └── cursor/                # Cursor overlays: agents(15), commands(11), hooks(3), rules(2)
├── brain/                     # Atelier Brain — Node.js MCP server + REST API
│   ├── server.mjs             # Entry point (MCP + HTTP modes)
│   ├── lib/                   # db, tools, rest-api, embed, consolidation, ttl, conflict, static, crash-guards
│   ├── ui/                    # dashboard.html(1760L), index.html(167L), settings.js(26KB), settings.css(400L)
│   ├── migrations/            # 9 PostgreSQL migration files
│   └── scripts/               # hydrate-telemetry.mjs, hydrate-enforcement.mjs
├── skills/                    # 7 skills: pipeline-setup(60KB), brain-setup(17KB), brain-hydrate(20KB), etc.
├── .claude/                   # Installed pipeline — 15 agents, 11 commands, 23 hooks, 5 rules, 16 references
├── .claude-plugin/            # Claude plugin manifest
├── .cursor-plugin/            # Cursor plugin manifest
├── tests/                     # 65 test files (51 pytest, 14 node --test), 1570+ tests
└── docs/                      # 67 docs (33 ADRs, 9 specs, 2 guides, 8 pipeline state)
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent/hook enforcement | Bash shell scripts (PreToolUse/PostToolUse) |
| Brain MCP server | Node.js (ES modules), @modelcontextprotocol/sdk ^1.27.1 |
| Brain persistence | PostgreSQL 17 + pgvector + ltree |
| Brain validation | zod ^3.24.0 |
| Brain UI | Vanilla HTML/CSS/JS — no framework, no build step |
| Agent personas | Markdown with YAML frontmatter |
| Test suite | pytest (Python) + node --test (Node.js mjs) |
| CI/CD | None configured |
| Linter | None configured |
| Type checker | None configured |

### Frontend (brain/ui/)

Single-file vanilla JS/HTML/CSS. Chart.js via CDN. Served by brain/lib/static.mjs with runtime token injection.
No UX spec baseline (docs/ux/ absent; partial spec in docs/brain/atelier-brain-settings-ux.md).

### Test Distribution

| Type | Files | Tests |
|------|-------|-------|
| pytest (Python) | 51 | 1570 collected |
| node --test (mjs) | 14 | N/A (node runner) |
| Total | 65 | 1570+ |

Test command: `pytest tests/ && cd brain && node --test ../tests/brain/*.test.mjs`
No linter. No type checker.

### Dependencies (brain/package.json only)

| Package | Version | Purpose |
|---------|---------|---------|
| @modelcontextprotocol/sdk | ^1.27.1 | MCP server protocol |
| pg | ^8.20.0 | PostgreSQL client |
| pgvector | ^0.2.1 | Vector similarity |
| zod | ^3.24.0 | Runtime validation |

Lockfile committed (package-lock.json, lockfileVersion 3). No CI/CD workflows. No Dockerfile (Docker Compose only for local db).

---

## Brain Context Summary (atelier-pipeline scoped)

Brain available: `true` (scope: `atelier.plugin`)

1. **Behavioral constraints are ineffective** — LLMs ignore NEVER rules. Fix: PreToolUse hooks with exit code 2. (lesson, importance: 1.0)

2. **v3.17.0 roundtable**: 9/12 mandatory gates had zero mechanical enforcement; colby_blocked_paths was dead code (Colby had unrestricted write access); core agent constant missing sentinel/darwin/deps; SessionStart hydration hook referenced in docs but didn't exist. Many fixed in ADR-0033. (insight, importance: 1.0, 2026-04-03)

3. **Infrastructure tier: Week One**: Session crash loses in-flight Tier 1 telemetry; no idempotency keys on mutating ops; no session-level cost ceiling (biggest structural risk). (insight, importance: 0.95)

4. **ADR-0023**: ~57% spec reduction — constraints over procedures. Distillator explicitly exempted. (decision)

5. **Plugin agents constraint**: Agents MUST live in project .claude/agents/, NOT plugin-native agents/ — Anthropic silently ignores hooks/mcpServers frontmatter on plugin-native agents. (decision, importance: 1.0)

6. **Gauntlet blocked Eva's Write tool**: enforce-eva-paths.sh has no accommodation for docs/reviews/ Gauntlet output directory — noted as architectural gap.

*Note: Many brain results were from syntetiq/clairvoyant.app scopes and have been filtered out.*

---

*End of Discovery. Round 1 (Cal) begins next.*
