# Pipeline State

<!-- PIPELINE_STATUS: {"phase": "idle", "sizing": null, "roz_qa": null, "telemetry_captured": false, "ci_watch_active": false, "ci_watch_retry_count": 0, "ci_watch_commit_sha": "", "poirot_reviewed": false, "robert_reviewed": false, "brain_available": false, "stop_reason": "completed_clean"} -->

## Prior Pipeline (closed)
**Feature:** Update ADR-0042 Roz structural hash baseline (pre-push fix)
**Phase:** idle
**Stop Reason:** completed_clean
**Sizing:** Micro
**Opened:** 2026-04-20
**Closed:** 2026-04-20
**Commit:** (see commit log)

**Scope:** Test-fixture maintenance. Update two hex strings in `tests/fixtures/adr_0042_baselines.py`:
- `CHANGED_AGENT_STRUCTURAL_HASHES["roz"]["claude"]`: `e46543d4…3f2` → `c4ab9a22…b34`
- `CHANGED_AGENT_STRUCTURAL_HASHES["roz"]["cursor"]`: `3ce2d101…a2b` → `298e317e…17c`

**Rationale:** ADR-0042's T_0042_019[roz] test locks a structural hash over Roz's frontmatter (stripping model:/effort: lines). The Roz maxTurns 15→50 bump landed in commit 1cda942 legitimately changed the hash. Update the baseline to match.

**Why now (before push):** We committed 3.38.0 locally as ff3b645. Pushing would ship a red test to CI. Fix the baseline first so the release commit arrives green.

**Micro skips:** scout fan-out, brain capture T2/T3, budget estimate gate. Roz full suite as safety valve (T_0042_019[roz] flip from red to green is the primary signal).

**Status:** Ellis commit complete. Push pending user confirmation (all four commits together: 1cda942, 8fd1e4f, ff3b645, this commit).

---

## Prior Pipeline (closed)
**Feature:** v3.38.0 release — version bump + CHANGELOG
**Phase:** idle
**Stop Reason:** completed_clean
**Sizing:** Micro
**Opened:** 2026-04-20
**Closed:** 2026-04-20
**Release:** v3.38.0 (see commit log)

**Scope:** Mechanical version bump using the new `scripts/release.sh` utility (dogfood).
- Run `./scripts/release.sh 3.38.0` — updates 5 version files
- Update `CHANGELOG.md` — rename `## [Unreleased]` block heading to `## [3.38.0] - 2026-04-20`
- Commit with `chore(release): bump version to 3.38.0` subject
- Push pending user confirmation (push is blast-radius — user decides)

**Contents of 3.38.0 release (from Unreleased block):** new `scripts/release.sh` utility + tests, marketplace.json sync fix, Roz effort parity fix, Roz maxTurns 15→50 (from prior pipeline 1cda942).

**Micro skips:** scout fan-out, brain capture T2/T3, budget estimate gate. Roz full suite as safety valve.

**Status:** Ellis commit complete. Push pending user confirmation.

---

## Prior Pipeline (closed)
**Feature:** Pre-release cleanup — Roz effort parity + marketplace.json sync + release script
**Phase:** idle
**Stop Reason:** completed_clean
**Sizing:** Small
**Opened:** 2026-04-20
**Closed:** 2026-04-20
**Commit:** (see commit log)

**Scope (3 concerns, 5 files + 1 test + CHANGELOG + pipeline state):**
1. `.claude/agents/roz.md` — `effort: high` → `medium` (match source template and pipeline-models.md Tier 3 base) ✓ landed
2. `.claude-plugin/marketplace.json` — `"version": "3.34.0"` → `"3.37.0"` (end users currently can't install 3.35/3.36/3.37 via Claude marketplace; stale since 3.34.0) ✓ landed
3. `scripts/release.sh` — NEW utility bumping all 5 version files in a single invocation ✓ landed

**Rationale:** Investigation revealed `.claude-plugin/marketplace.json` was missed in every release commit from 3.35.0 onward. The 5 version files drift apart silently. Adding a release script mechanically prevents the class of error; updating marketplace.json to 3.37.0 clears the current lag.

**Progress:**
- Colby build v1: complete
- Roz safety-valve sweep: PASS
- Poirot blind review v1: CONCERNS — 4 FIX-REQUIRED items on release.sh/tests/CHANGELOG
- Colby rework: complete (strict semver regex, 9 parametrized rejection cases, nested-keys pin, CHANGELOG atomicity wording softened)
- Roz scoped re-run: PASS (13/13 tests, all findings resolved, no collateral damage)
- Poirot blind re-review: PASS (CONCERNS log-level only — ship-gate clear)
- Ellis commit: complete

**Out of scope:**
- Local plugin cache pollution at `~/.claude/plugins/cache/atelier-pipeline/atelier-pipeline/{3.36.0,3.37.0}` — local maintenance, not a code change. User will `rm -rf` separately.
- Bumping to 3.38.0 — user will do that as a follow-up once cleanup lands.
- `docs/pipeline/error-patterns.md` `unknown/unknown` telemetry noise (Poirot finding #7) — upstream capture hygiene, separate concern.

**Small ceremony:** Scout fan-out for Colby done. Roz full suite + scoped rework re-verify. Poirot blind diff review done (rework cycle got focused re-check). No Cal (no architectural decision). No Robert (Small skips review-juncture Robert gate).
---

## Prior Pipeline (closed)
**Feature:** Roz maxTurns bump (15 → 50) — fix turn-cap truncation mid-generation
**Phase:** idle
**Stop Reason:** completed_clean
**Sizing:** Micro
**Opened:** 2026-04-20
**Closed:** 2026-04-20
**Commit:** (see commit log)

**Scope:** Frontmatter edits (maxTurns: 15 → 50):
- `.claude/agents/roz.md` (installed)
- `source/claude/agents/roz.frontmatter.yml` (source template)
- `source/cursor/agents/roz.frontmatter.yml` (source template, synced down for parity)
- Closed pipeline-state.md itself in same commit.

**Rationale:** Roz hit 15-turn ceiling and truncated mid-sentence on tool-heavy QA runs. Peer agents are at 40–75; Roz=15 is a documented outlier. 50 matches peer range (agatha=60, cal=45, colby=75).

**Out of scope:** validate-dod-marker.sh hook (confirmed orphan artifact from abandoned Apr 17 iteration; not in git; shipped in local plugin cache only). `effort` discrepancy between roz.md (high) and source yml (medium) — tracked separately.

**Micro skips:** scout fan-out for Colby, brain capture T2/T3, budget estimate gate. Roz full suite still runs as safety valve.

---

## Prior Pipeline (closed)
**Feature:** v3.35.0 release — version bump + CHANGELOG
**Phase:** idle
**Stop Reason:** completed_clean
**Sizing:** Micro
**Closed:** 2026-04-17

---

## Prior Pipeline (closed)
**Feature:** Pre-existing test suite failures — 87 hooks + 4 xml-prompt-structure
**Phase:** idle
**Stop Reason:** completed_clean
**Sizing:** Small
**Closed:** 2026-04-16
**Commit:** 3c8e7cb

---

## Prior Pipeline (closed)
**Feature:** ADR-0041 — Effort-per-agent task-class tier model (Opus 4.7 xhigh)
**Stop Reason:** completed_clean
**Closed:** 2026-04-16
**Release:** v3.34.0 (commit df47b85)
**Resolved:** GitHub issue #41

**Telemetry T3:** rework=3 cycles, first_pass_qa=0.25, evoscore=1.039 (+60 net new tests). Captured as brain thought 67fccb53.

**Key decision captured:** 4-tier task-class model replaces size-dependent model tables + universal scope classifier. Priority stack: accuracy > speed > cost. Sonnet eliminated from reasoning tiers. Supersedes brain thought b09f430b (Colby Medium=Opus, 2026-04-03).

**Known pattern:** Roz partial-output stall recurred 3× this session. Mitigation: Eva-run pytest diagnostic bridges the gap. Captured as lesson d70409af. Structural fix candidate: explicit "STOP and RETURN" constraint in Roz persona.

---

## Prior Pipeline (closed)
**Feature:** ADR-0040 Design system auto-loading + Cal institutional memory search
**Stop Reason:** completed_clean
**Closed:** 2026-04-13
**Release:** v3.33.0 (commit e5686ab)

## Prior Pipeline (closed)
**Feature:** feat/brain-setup-auto-fix
**Stop Reason:** completed_clean
**Closed:** 2026-04-13
**Release:** v3.30.7

## Prior Pipeline (closed)
**Feature:** ADR-0035 + ADR-0036 + ADR-0037 — Waves 4, 5, 6
**Stop Reason:** completed_clean
**Closed:** 2026-04-12
**Release:** v3.29.0

## Prior Pipeline (closed)
**Feature:** ADR-0034 Gauntlet remediation
**Stop Reason:** completed_clean
**Closed:** 2026-04-12
**Release:** v3.28.0
</content>
</invoke><!-- COMPACTION: 2026-04-17T02:23:07Z -->
<!-- COMPACTION: 2026-04-17T03:08:07Z -->
