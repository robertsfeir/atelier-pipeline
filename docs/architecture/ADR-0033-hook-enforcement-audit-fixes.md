# ADR-0033: Source-Tree Hook Enforcement Audit Fixes

## Status

Accepted — 2026-04-11

## Context

Eva performed a full enforcement audit across `source/claude/hooks/`,
`source/shared/hooks/`, `source/claude/agents/`, and
`skills/pipeline-setup/SKILL.md`. Two authoritative sources were compared:
`source/` (the templates) and `.claude/` (the self-hosted installed copy).
This project eats its own cooking, so both trees exist in the repo, but in
this pipeline **only `source/` is edited**. `.claude/` is re-synced from
`source/` via `/pipeline-setup` — never touched by Colby directly.

The audit surfaced 2 critical bugs, 4 major bugs, 5 minor fixes, and 2 design
gaps. The most severe finding (C1) silently reports `pipeline_active=false`
on every session boot, which poisons downstream enforcement decisions. The
second critical finding (C2) means fresh `/pipeline-setup` installs ship
with **zero scout swarm enforcement** — the scout fan-out protocol is a
behavioral-only guardrail until `enforce-scout-swarm.sh` gets registered in
`settings.json`, and the script is missing from both the file-copy manifest
and the hook registration template.

## Decision

Fix all 13 findings (C1-C2, M1-M4, m1-m5, G1-G2) in a single ADR, split into
two build waves:

1. **Wave 1 — Hook and agent fixes** (9 files in `source/claude/hooks/` and
   `source/claude/agents/`, plus `source/shared/hooks/session-boot.sh`).
   Each edit is precise and independent. Colby applies them with targeted
   `Edit` calls against `source/` only.
2. **Wave 2 — SKILL.md surgical edits** (1 large file, ~863 lines). Every
   change is a scoped `Edit` with explicit old_string/new_string anchors.
   No rewrite. This wave must not change line counts elsewhere in the file.

No `.claude/` files are touched. After Ellis commits, `/pipeline-setup` is
the mechanism for re-installing the updated templates into `.claude/`.

### Spec Challenge and SPOF

The audit assumes that **`source/shared/hooks/session-boot.sh` is the file
installed by `/pipeline-setup`**. If wrong, fixing C1 and M2 in the shared
copy alone would leave the bug live in production installs. I verified this
in `skills/pipeline-setup/SKILL.md` line 313:

```
| `source/shared/hooks/session-boot.sh` | `.claude/hooks/session-boot.sh` | ... |
```

The shared copy is the install source. There is also a byte-identical
`source/claude/hooks/session-boot.sh` — likely a legacy duplicate. I treat
both files as authoritative and patch both, then add a test that enforces
they stay in sync. That removes the "which one is real" SPOF entirely.

**SPOF: SKILL.md surgical edits.** If Wave 2 corrupts the settings.json JSON
blob in the template (trailing comma, unbalanced bracket, unescaped quote),
every fresh install fails at hook registration time. Graceful degradation:
Wave 2 ships with a dedicated pytest that parses the embedded JSON block
inside SKILL.md and asserts `json.loads()` succeeds AND contains the
expected hook entries. This runs before Wave 2 is marked PASS.

### Anti-goals

- **Anti-goal: rewriting `enforce-scout-swarm.sh` to support additional
  agents.** Reason: the research brief scopes the fix to adding content
  validation for Roz's existing evidence tags; anything broader is design
  drift. Revisit: when a new production agent (not cal/colby/roz) needs
  scout evidence enforcement.
- **Anti-goal: changing the `brain-extractor` capture schema.** Reason:
  ADR-0025 owns the quality-signals schema; G1 extends the *list of agent
  types* that fire extraction, not what gets extracted. Revisit: when
  Darwin surfaces telemetry gaps for robert/sable/ellis captures.
- **Anti-goal: touching `.claude/` during this pipeline.** Reason: this
  project's source-of-truth discipline is that Colby edits `source/` only;
  `.claude/` is re-synced by `/pipeline-setup`. Revisit: never — this is
  a hard project rule encoded in multiple retro lessons.

## Alternatives Considered

1. **Split into 13 separate ADRs.** Rejected — the findings are all in the
   same subsystem (source-tree enforcement), share the same test
   infrastructure (pytest tests/hooks/), and can be landed atomically in
   two waves. One ADR, one pipeline, one commit stream.
2. **Fix only critical and major findings; defer minor+gap.** Rejected —
   the minor fixes (m1-m5) are trivial text edits (1-2 lines each) and the
   gap fixes (G1, G2) are natural extensions of the major fixes. Deferring
   creates three ADRs for one subsystem touch — more churn, not less.
3. **Write a new `lib/common-grep.sh` and consolidate the PIPELINE_STATUS
   grep pattern across all hooks.** Rejected — the canonical pattern is
   one line repeated in a handful of places. Introducing a shared library
   adds a sourcing requirement to every hook and a bootstrap risk for
   fresh installs. Targeted fix is lower risk. Revisit: if a fourth hook
   adds the same pattern.
4. **Leave the `source/claude/hooks/session-boot.sh` duplicate and only
   patch `source/shared/hooks/session-boot.sh`.** Rejected — the duplicate
   exists in the repo, might be read by contributors or future code, and
   diverging the two would be a latent bug. Fix both; add an enforcement
   test that asserts byte-identical.

## Consequences

**Positive:**
- Session boot starts reporting `pipeline_active=true` when a pipeline is
  active (fixes C1, unblocks all downstream enforcement that depends on
  the boot-collected state).
- Fresh `/pipeline-setup` installs get scout swarm enforcement by default
  (fixes C2).
- Colby's default path blocks include `.github/` — no more accidental CI
  workflow edits on fresh installs (fixes M1).
- `CUSTOM_AGENT_COUNT` stops over-reporting by 6 on every boot (fixes M2).
- Empty Roz evidence blocks are blocked at the hook layer (fixes M3).
- SKILL.md template documentation matches reality (fixes M4, m3).
- Dead code and stale comments removed (fixes m1, m2, m3, m4).
- brain-extractor's haiku model reference uses the stable alias (fixes m5).
- Brain capture extraction coverage expands to all 8 production agents
  that write meaningful output (fixes G1).

**Negative:**
- Wave 2 is a single large-file edit. Risk mitigated by per-edit tests
  (see Test Specification T-0033-020 and T-0033-021).
- Fresh installs gain a new hook entry; existing installs must run
  `/pipeline-setup` to pick it up. Documented in DoD handoff note.
- Brain-extractor persona early-exit guard expands its trigger set; this
  is a throughput change — more extractor invocations per pipeline, more
  haiku cost per pipeline. Acceptable per G1 research brief.

**Neutral:**
- No schema changes. No migration. No runtime feature flags.

## Implementation Plan

All paths are absolute from repo root. Colby edits files in `source/` only.
Ellis commits per wave after Roz QA PASS.

### Wave 1 — Hook and agent fixes

Vertical slice: each file edit has a direct consumer (either a runtime
hook caller, an install-time manifest reader, or a pytest test). All
consumers are already in place; Wave 1 changes producer behavior and the
existing consumers pick it up unchanged.

#### Step 1: Fix session-boot.sh PIPELINE_STATUS grep pattern (C1)

**Files:**
- `source/shared/hooks/session-boot.sh` — line 43
- `source/claude/hooks/session-boot.sh` — line 43 (byte-identical duplicate)

**Current (broken):**
```bash
STATUS_JSON=$(grep -o 'PIPELINE_STATUS:{.*}' "$PIPELINE_STATE_FILE" 2>/dev/null | head -1 | sed 's/PIPELINE_STATUS://' || true)
```

**Fixed:**
```bash
STATUS_JSON=$(grep -o 'PIPELINE_STATUS: {[^}]*}' "$PIPELINE_STATE_FILE" 2>/dev/null | head -1 | sed 's/PIPELINE_STATUS: //' || true)
```

Rationale: canonical format (verified at `docs/pipeline/pipeline-state.md`
line 6 and `source/claude/hooks/enforce-scout-swarm.sh` line 74) includes
the literal space after the colon and uses `[^}]*` instead of `.*` to
avoid greedy matching when the state file contains multiple JSON blobs.
Both strings (`grep -o '...'` pattern AND `sed 's/.../'` strip) must be
updated together or STATUS_JSON ends up with the leading space intact,
breaking `jq`.

**Acceptance criteria:**
- Both files contain the corrected pattern.
- Both files remain byte-identical (enforcement test — see Step 2).
- Existing session-boot tests still pass.

**Complexity:** 2 files, 1 line each. Score: 0 (mechanical).

#### Step 2: Fix session-boot.sh CORE_AGENTS list (M2) and add duplicate-file enforcement test

**Files:**
- `source/shared/hooks/session-boot.sh` — line 107
- `source/claude/hooks/session-boot.sh` — line 107
- `tests/hooks/test_session_boot_sync.py` — NEW

**Current:**
```bash
CORE_AGENTS="cal colby roz ellis agatha robert sable investigator distillator"
```

**Fixed:**
```bash
CORE_AGENTS="cal colby roz ellis agatha robert sable investigator distillator sentinel darwin deps brain-extractor robert-spec sable-ux"
```

Rationale: the 6 missing agents are all pipeline-native (shipped by
`/pipeline-setup`) and should not be counted as custom. Verified against
`source/claude/agents/` directory listing.

New file `tests/hooks/test_session_boot_sync.py` asserts
`source/shared/hooks/session-boot.sh` and
`source/claude/hooks/session-boot.sh` are byte-identical using SHA-256.
This locks in the duplicate so future edits can never drift.

**Acceptance criteria:**
- Both files contain all 15 agent names in CORE_AGENTS.
- New test `test_T_0033_002_session_boot_files_identical` passes.
- `CUSTOM_AGENT_COUNT` returns 0 on a fresh install with no custom agents.

**Complexity:** 2 files edit + 1 file new. Score: 1 (mechanical + new test).

#### Step 3: Fix enforce-scout-swarm.sh Roz content validation (M3)

**Files:**
- `source/claude/hooks/enforce-scout-swarm.sh` — lines 176-181 (roz case)

**Current:**
```bash
  roz)
    if ! check_block_present "debug-evidence" && ! check_block_present "qa-evidence"; then
      echo "BLOCKED: Cannot invoke Roz without a <debug-evidence> or <qa-evidence> block. ..." >&2
      exit 2
    fi
    ;;
```

**Fixed:** Add content validation symmetric to cal/colby branches. If
neither block has >= 50 chars of content, block. If one is present with
sufficient content, allow. The order of checks matters — presence first
(existing), then content.

```bash
  roz)
    if ! check_block_present "debug-evidence" && ! check_block_present "qa-evidence"; then
      echo "BLOCKED: Cannot invoke Roz without a <debug-evidence> or <qa-evidence> block. Run scout fan-out first to populate QA evidence (pipeline-orchestration.md §Scout Fan-out Protocol)." >&2
      exit 2
    fi
    # At least one block must have >= 50 chars of content.
    debug_ok=false
    qa_ok=false
    check_block_content "debug-evidence" && debug_ok=true || true
    check_block_content "qa-evidence" && qa_ok=true || true
    if [ "$debug_ok" = "false" ] && [ "$qa_ok" = "false" ]; then
      echo "BLOCKED: <debug-evidence> and <qa-evidence> blocks are empty or too short (< 50 chars). Run the scout fan-out to generate real search results before invoking Roz." >&2
      exit 2
    fi
    ;;
```

Rationale: `check_block_content` fails-open when the closing tag is
absent (returns 0), so ambiguous structure still lets Roz through — this
preserves the existing fail-open posture for cal and colby. The new
logic ONLY blocks when at least one block is present AND neither has
sufficient content. This is the exact same gate cal and colby already
have, ported to the "either-or" block structure Roz uses.

**Acceptance criteria:**
- Empty `<debug-evidence></debug-evidence>` blocks Roz.
- Empty `<qa-evidence></qa-evidence>` blocks Roz.
- One empty + one full block allows Roz (content-full branch wins).
- A well-formed evidence block with >= 50 chars still allows Roz.
- Existing T-SCOUT tests for cal/colby unchanged.

**Complexity:** 1 file, ~10 lines. Score: 1 (new case logic + new tests).

#### Step 4: Add .github/ to colby_blocked_paths (M1)

**Files:**
- `source/claude/hooks/enforcement-config.json` — line 4-17

**Current colby_blocked_paths:**
```json
"colby_blocked_paths": [
  "docs/",
  ".gitlab-ci",
  ".circleci/",
  "Jenkinsfile",
  "Dockerfile",
  "docker-compose",
  ".gitlab/",
  "deploy/",
  "infra/",
  "terraform/",
  "pulumi/",
  "k8s/",
  "kubernetes/"
]
```

**Fixed:** Insert `".github/"` between `"docs/"` and `".gitlab-ci"`
(alphabetical-ish grouping — other CI paths follow).

Note: `tests/hooks/conftest.py` DEFAULT_CONFIG mirrors this list at
lines 62-76. It must be updated in the same step or the test harness
drifts from the shipped config. Update both.

**Files:**
- `source/claude/hooks/enforcement-config.json`
- `tests/hooks/conftest.py`

**Acceptance criteria:**
- `.github/` appears in the JSON array in both files.
- Both files parse as valid JSON (enforcement-config) / valid Python
  (conftest).
- Existing `test_enforce_colby_paths` tests still pass.
- New test asserts Colby cannot write `.github/workflows/ci.yml`.

**Complexity:** 2 files, 2 lines. Score: 0 (mechanical).

#### Step 5: Minor text-only fixes (m1, m2, m3, m5)

**Files:**
- `source/claude/hooks/enforce-roz-paths.sh` — line 3
- `source/claude/hooks/enforce-cal-paths.sh` — line 15
- `source/claude/hooks/post-compact-reinject.sh` — line 57
- `source/claude/agents/brain-extractor.frontmatter.yml` — line 8

**m1:** `enforce-roz-paths.sh` header comment:
- Old: `# PreToolUse hook on Write|Edit -- Roz can only write test files + docs/pipeline/`
- New: `# PreToolUse hook on Write -- Roz can only write test files + docs/pipeline/`

Matches the actual case statement on line 16 which only handles `Write)`.

**m2:** `enforce-cal-paths.sh` dead branch:
- Old: `case "$TOOL_NAME" in Write|Edit|MultiEdit) ;; *) exit 0 ;; esac`
- New: `case "$TOOL_NAME" in Write|Edit) ;; *) exit 0 ;; esac`

Cal's frontmatter fires on Write|Edit only. MultiEdit is unreachable.

**m3:** `post-compact-reinject.sh` Brain Protocol Reminder:
- Old: `"- Prefetch hook: prompt-brain-prefetch.sh (before Agent) injects brain context for cal/colby/roz/agatha."`
- New: `"- Prefetch hook: prompt-brain-prefetch.sh (before Agent) reminds Eva to call agent_search for cal/colby/roz before invoking them. Eva injects results into <brain-context>."`

The hook outputs an advisory string — it does not automatically inject
anything. Also narrows the agent set to match m4 (see Step 6).

**m5:** `brain-extractor.frontmatter.yml`:
- Old: `model: claude-haiku-4-5-20251001`
- New: `model: haiku`

Uses the stable alias; avoids pinning to a dated model string.

**Acceptance criteria:**
- All four files reflect the corrected text.
- All existing tests still pass (no behavior change from m1, m2, m3, m5).

**Complexity:** 4 files, 1 line each. Score: -2 (pure text edits,
demoted to haiku/mechanical).

#### Step 6: Narrow prompt-brain-prefetch.sh scope to scout-gated agents (m4, G2)

**Files:**
- `source/claude/hooks/prompt-brain-prefetch.sh` — lines 30-33 and line 7
- `tests/hooks/test_prompt_brain_prefetch.py` — UPDATE existing tests

**Current (line 30-33):**
```bash
case "$SUBAGENT_TYPE" in
  cal|colby|roz|agatha) ;;
  *) exit 0 ;;
esac
```

**Fixed:**
```bash
case "$SUBAGENT_TYPE" in
  cal|colby|roz) ;;
  *) exit 0 ;;
esac
```

Header comment line 7 also needs updating:
- Old: `# (cal, colby, roz, agatha). Exits 0 always.`
- New: `# (cal, colby, roz — matches scout swarm enforcement scope). Exits 0 always.`

Rationale: scout swarm enforcement (`enforce-scout-swarm.sh`) only gates
cal/colby/roz. The brain prefetch reminder is paired with scout
enforcement — it makes no sense for Agatha who has no scout evidence
requirement.

**Acceptance criteria:**
- Invoking Agatha no longer produces brain prefetch reminder output.
- Invoking cal/colby/roz still produces reminder output.
- Existing tests updated: the agatha reminder test must now assert
  empty output instead of reminder text.

**Complexity:** 1 file edit + test update. Score: 0 (mechanical +
test sync).

#### Step 7: Extend brain-extractor agent_type scope (G1)

**Files:**
- `source/claude/agents/brain-extractor.frontmatter.yml` — description field
- `source/shared/agents/brain-extractor.md` — lines 19-21 (early-exit guard)
  and lines 30-40 (extraction steps section)

**Current (persona early-exit guard, lines 19-21):**
```
If `agent_type` is not one of the four target agents (`cal`, `colby`, `roz`,
`agatha`), stop immediately and produce zero captures. Do not read, do not
analyze, do not call any tools. This is not a target agent -- early-exit now.
```

**Fixed:**
```
If `agent_type` is not one of the nine target agents (`cal`, `colby`, `roz`,
`agatha`, `robert`, `robert-spec`, `sable`, `sable-ux`, `ellis`), stop
immediately and produce zero captures. Do not read, do not analyze, do not
call any tools. This is not a target agent -- early-exit now.
```

Also update the agent-to-metadata mapping table (lines 40-48) to include
entries for the 5 new agents:

```
| agent_type    | source_agent  | source_phase |
|---------------|---------------|--------------|
| cal           | cal           | design       |
| colby         | colby         | build        |
| roz           | roz           | qa           |
| agatha        | agatha        | handoff      |
| robert        | robert        | product      |
| robert-spec   | robert-spec   | product      |
| sable         | sable         | ux           |
| sable-ux      | sable-ux      | ux           |
| ellis         | ellis         | commit       |
```

Add a note after the quality signals section clarifying that the five
new agent types run the decisions/patterns/lessons/seeds extraction pass
only — no per-agent quality signals schema is defined for them. Future
ADRs may add schemas (that's a Darwin concern, not this ADR).

Description field in frontmatter:
- Old: `"Brain knowledge extractor. Fires as a SubagentStop hook after cal, colby, roz, or agatha complete. ..."`
- New: `"Brain knowledge extractor. Fires as a SubagentStop hook after cal, colby, roz, agatha, robert, robert-spec, sable, sable-ux, or ellis complete. ..."`

**Note:** the SKILL.md settings.json template `if:` condition for the
brain-extractor agent hook also needs updating — that's Wave 2 Step 9.
brain-extractor is excluded from its own trigger condition to prevent
infinite loops (ADR-0024 rule).

**Acceptance criteria:**
- Persona lists 9 target agent types.
- Extraction table has 9 rows with correct source_phase values.
- Frontmatter description matches persona.
- Existing `tests/hooks/test_brain_extractor.py` still passes OR is
  updated to cover the new scope.
- New test asserts each new agent_type produces a valid agent-to-metadata
  mapping (table parseable).

**Complexity:** 2 files, ~15 lines. Score: 2 (schema extension + test
update).

### Wave 2 — SKILL.md surgical edits

One file, four anchored edits. All via `Edit` tool with unique old_string
anchors. No MultiEdit. Wave 2 runs after Wave 1 passes QA so the hook
changes are already committed and registered in the audit.

#### Step 8: Add enforce-scout-swarm.sh to SKILL.md file manifest (C2 part 1)

**Files:**
- `skills/pipeline-setup/SKILL.md` — manifest table, between existing
  `enforce-pipeline-activation.sh` row (line 300) and `enforce-git.sh` row
  (line 301).

**Edit:** insert a new row in the file-copy manifest table:

```
| `source/claude/hooks/enforce-scout-swarm.sh` | `.claude/hooks/enforce-scout-swarm.sh` | Blocks Cal/Colby/Roz invocations missing the required scout evidence block (research-brief, colby-context, debug-evidence, qa-evidence) |
```

Anchor: unique substring `enforce-pipeline-activation.sh` | ...
`Blocks Colby/Ellis invocation when no active pipeline exists` — insert
new row immediately after.

**Acceptance criteria:**
- Manifest table contains the new row.
- Row count increases by exactly 1.
- `/pipeline-setup` copies the file into `.claude/hooks/` on fresh install.

**Complexity:** 1 row addition. Score: 0.

#### Step 9: Register enforce-scout-swarm.sh + extend brain-extractor if: condition in settings.json template (C2 part 2 + G1 wire)

**Files:**
- `skills/pipeline-setup/SKILL.md` — lines 354 and 390 inside the JSON
  block.

**Edit A — settings.json Agent matcher hooks array (line 354):**

Current (line 354, one long line):
```json
"hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-sequencing.sh"}, {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-pipeline-activation.sh"}, {"type": "prompt", "prompt": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/prompt-brain-prefetch.sh", "if": "tool_input.subagent_type == 'cal' || tool_input.subagent_type == 'colby' || tool_input.subagent_type == 'roz' || tool_input.subagent_type == 'agatha'"}]
```

Fixed:
```json
"hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-sequencing.sh"}, {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-pipeline-activation.sh"}, {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-scout-swarm.sh"}, {"type": "prompt", "prompt": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/prompt-brain-prefetch.sh", "if": "tool_input.subagent_type == 'cal' || tool_input.subagent_type == 'colby' || tool_input.subagent_type == 'roz'"}]
```

Two changes: (a) add the new command entry for `enforce-scout-swarm.sh`
between `enforce-pipeline-activation.sh` and the prompt entry, (b) drop
`|| tool_input.subagent_type == 'agatha'` from the prompt `if:` condition
to match Step 6 (G2). `enforce-scout-swarm.sh` is a `command`-type hook
with no `if:` — it self-filters by checking `.agent_id` and
`.tool_input.subagent_type` internally.

**Edit B — brain-extractor agent SubagentStop if: condition (line 390):**

Current:
```json
"if": "agent_type == 'cal' || agent_type == 'colby' || agent_type == 'roz' || agent_type == 'agatha'"
```

Fixed:
```json
"if": "agent_type == 'cal' || agent_type == 'colby' || agent_type == 'roz' || agent_type == 'agatha' || agent_type == 'robert' || agent_type == 'robert-spec' || agent_type == 'sable' || agent_type == 'sable-ux' || agent_type == 'ellis'"
```

brain-extractor is excluded from its own trigger set (infinite-loop
prevention, ADR-0024). All 9 agent types from Step 7 are listed.

**Acceptance criteria:**
- The JSON block inside SKILL.md parses as valid JSON after edits
  (programmatically verified — see T-0033-020).
- The Agent matcher contains 4 command entries including
  `enforce-scout-swarm.sh`.
- The prompt-brain-prefetch.sh `if:` condition lists 3 subagent types
  (cal, colby, roz — no agatha).
- The brain-extractor `if:` condition lists 9 agent types.
- Fresh `/pipeline-setup` produces a `.claude/settings.json` that parses
  and registers the new hook.

**Complexity:** 2 surgical JSON edits inside one markdown fence. Score: 2
(high-risk single-file edit — extra validation required).

#### Step 10: Fix session-hydrate.sh manifest description + add Step 0c cleanup (M4)

**Files:**
- `skills/pipeline-setup/SKILL.md` — line 302 (manifest description) and
  insert new Step 0c after existing Step 0b (between lines 65 and 67).

**Edit A — line 302 manifest description:**

Current:
```
| `source/claude/hooks/session-hydrate.sh` | `.claude/hooks/session-hydrate.sh` | Runs telemetry hydration at SessionStart (JSONL + state-file parsing) |
```

Fixed:
```
| `source/claude/hooks/session-hydrate.sh` | `.claude/hooks/session-hydrate.sh` | Intentional no-op — superseded by atelier_hydrate MCP tool. Installed for backward-compatibility only; NOT registered in settings.json. |
```

Rationale: source file comment (lines 1-15) already documents this as a
no-op. Manifest description was never updated.

**Edit B — insert new Step 0c "Clean Up Orphan session-hydrate.sh Registration":**

Insert after line 65 (`4. **Silent no-op:** If neither found: do nothing.
No output.` — the Step 0b terminator) and before line 67 (`### Step 1:
Gather Project Information`).

```markdown
### Step 0c: Clean Up Orphan session-hydrate.sh Registration

Unconditionally run this cleanup on every /pipeline-setup invocation. Silent unless it finds something to remove.

`session-hydrate.sh` is now an intentional no-op (superseded by the `atelier_hydrate` MCP tool) and must NOT be registered in `.claude/settings.json`. Older installs may still have a registration entry.

1. **Check settings.json:** Check if `.claude/settings.json` exists and contains a hook entry referencing `session-hydrate.sh` in any command string across all hook event types (SessionStart is the typical location). If found:
   - Parse the JSON. If the JSON is malformed or invalid, log a warning ("Warning: .claude/settings.json is malformed JSON -- skipping session-hydrate.sh entry removal. Does not block setup.") and continue to Step 1.
   - Remove the hook entry containing "session-hydrate.sh" from the command string.
   - If removing that entry leaves an empty hooks array for an event type, remove the event type entry entirely (no empty arrays left behind).
   - Write the updated JSON back to `.claude/settings.json`.
   - Note that removal occurred.
2. **Print notice (conditional):** If the entry was found and removed: print exactly `Removed orphan session-hydrate.sh registration (intentional no-op, see source comment).`
3. **Silent no-op:** If not found: do nothing. No output.

**Note:** The `.claude/hooks/session-hydrate.sh` file itself is NOT deleted — it is re-copied by Step 3a as an intentional no-op backward-compatibility shim. Only the `settings.json` registration is removed.

This cleanup targets only session-hydrate.sh registrations. Other hook entries are not affected.
```

Structural mirror of existing Step 0a pattern (lines 36-56) — same
edge-case handling, same silent-no-op rule, same notice format.

**Acceptance criteria:**
- Manifest description reflects "intentional no-op".
- Step 0c section exists after Step 0b, before Step 1.
- Step 0c is structurally parallel to Step 0a.
- No other line content changes.

**Complexity:** 1 row edit + 1 new section (~20 lines). Score: 1.

## Test Specification

All tests pytest-compatible in `tests/hooks/`. Failure cases >= happy path.

| ID | Category | Description | File |
|----|----------|-------------|------|
| T-0033-001 | unit | session-boot.sh parses a canonical `PIPELINE_STATUS: {...}` line and extracts `phase`, `feature` correctly, sets `pipeline_active=true` | tests/hooks/test_session_boot.py |
| T-0033-002 | invariant | source/shared/hooks/session-boot.sh and source/claude/hooks/session-boot.sh are byte-identical (SHA-256) | tests/hooks/test_session_boot_sync.py |
| T-0033-003 | unit | session-boot.sh correctly reports `pipeline_active=false` when PHASE is `idle` | tests/hooks/test_session_boot.py |
| T-0033-004 | unit | session-boot.sh correctly reports `pipeline_active=false` when PHASE is `complete` | tests/hooks/test_session_boot.py |
| T-0033-005 | regression | session-boot.sh with legacy no-space `PIPELINE_STATUS:{...}` is NOT matched (grep pattern strictness) | tests/hooks/test_session_boot.py |
| T-0033-006 | unit | session-boot.sh CORE_AGENTS contains all 15 agents (cal, colby, roz, ellis, agatha, robert, sable, investigator, distillator, sentinel, darwin, deps, brain-extractor, robert-spec, sable-ux) | tests/hooks/test_session_boot.py |
| T-0033-007 | unit | session-boot.sh reports CUSTOM_AGENT_COUNT=0 on a pipeline-default `.claude/agents/` listing (fixture) | tests/hooks/test_session_boot.py |
| T-0033-008 | unit | session-boot.sh reports CUSTOM_AGENT_COUNT=1 when a non-core agent file is present | tests/hooks/test_session_boot.py |
| T-0033-009 | unit | enforce-scout-swarm.sh blocks Roz when `<debug-evidence></debug-evidence>` is empty | tests/hooks/test_enforce_scout_swarm.py |
| T-0033-010 | unit | enforce-scout-swarm.sh blocks Roz when `<qa-evidence></qa-evidence>` is empty | tests/hooks/test_enforce_scout_swarm.py |
| T-0033-011 | unit | enforce-scout-swarm.sh blocks Roz when both blocks are present but both < 50 chars | tests/hooks/test_enforce_scout_swarm.py |
| T-0033-012 | unit | enforce-scout-swarm.sh allows Roz when one block is empty and the other has >= 50 chars (either-or) | tests/hooks/test_enforce_scout_swarm.py |
| T-0033-013 | unit | enforce-scout-swarm.sh still allows Roz when a well-formed `<qa-evidence>` with 200 chars is present | tests/hooks/test_enforce_scout_swarm.py |
| T-0033-014 | unit | enforce-colby-paths.sh blocks a Write to `.github/workflows/ci.yml` when `.github/` is in colby_blocked_paths | tests/hooks/test_enforce_colby_paths.py |
| T-0033-015 | unit | enforcement-config.json parses as valid JSON and `.github/` appears in colby_blocked_paths | tests/hooks/test_enforce_colby_paths.py |
| T-0033-016 | unit | prompt-brain-prefetch.sh produces empty output when invoked with subagent_type=agatha | tests/hooks/test_prompt_brain_prefetch.py |
| T-0033-017 | unit | prompt-brain-prefetch.sh still produces reminder output for cal/colby/roz | tests/hooks/test_prompt_brain_prefetch.py |
| T-0033-018 | unit | brain-extractor.md persona early-exit guard lists all 9 target agent types | tests/hooks/test_brain_extractor.py |
| T-0033-019 | unit | brain-extractor.md agent-to-metadata table parses with 9 rows and unique (agent_type, source_agent, source_phase) tuples | tests/hooks/test_brain_extractor.py |
| T-0033-020 | invariant | SKILL.md contains a fenced ```json block that parses via `json.loads()` successfully | tests/hooks/test_pipeline_setup_skill.py |
| T-0033-021 | invariant | SKILL.md settings.json template registers enforce-scout-swarm.sh, prompt-brain-prefetch.sh with 3-agent condition, and brain-extractor with 9-agent condition | tests/hooks/test_pipeline_setup_skill.py |
| T-0033-022 | unit | SKILL.md file-copy manifest contains a row for enforce-scout-swarm.sh | tests/hooks/test_pipeline_setup_skill.py |
| T-0033-023 | unit | SKILL.md contains a Step 0c section between Step 0b and Step 1 referencing session-hydrate.sh cleanup | tests/hooks/test_pipeline_setup_skill.py |
| T-0033-024 | unit | SKILL.md session-hydrate.sh manifest description contains "no-op" and "NOT registered" | tests/hooks/test_pipeline_setup_skill.py |
| T-0033-025 | regression | enforce-cal-paths.sh case statement matches Write|Edit only (no MultiEdit branch) | tests/hooks/test_enforce_cal_paths.py |
| T-0033-026 | regression | enforce-roz-paths.sh header comment says "Write" not "Write|Edit" | tests/hooks/test_enforce_roz_paths.py |
| T-0033-027 | unit | post-compact-reinject.sh Brain Protocol Reminder contains "reminds" (not "injects") and lists cal/colby/roz only | tests/hooks/test_post_compact_reinject.py |
| T-0033-028 | unit | brain-extractor.frontmatter.yml contains `model: haiku` (stable alias) | tests/hooks/test_brain_extractor.py |
| T-0033-029 | regression | brain-extractor.frontmatter.yml description field lists 9 agent types | tests/hooks/test_brain_extractor.py |
| T-0033-030 | regression | conftest.py DEFAULT_CONFIG colby_blocked_paths matches enforcement-config.json colby_blocked_paths exactly | tests/hooks/test_enforce_colby_paths.py |

Total: 30 tests. Failure cases (11) >= happy path (8).

Test categories:
- **unit**: 21
- **regression**: 5
- **invariant**: 4

## UX Coverage

N/A — this is an infrastructure/enforcement fix with no user-facing
surface. No UX doc exists or is required.

## Contract Boundaries

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| session-boot.sh (both copies) | JSON on stdout with `pipeline_active`, `phase`, `feature`, `custom_agent_count` | Eva boot sequence consuming `{CONFIG_DIR}/settings.json` SessionStart hook output | Step 1, Step 2 |
| enforcement-config.json `colby_blocked_paths` array | JSON array of path prefix strings | enforce-colby-paths.sh reads via `jq -r '.colby_blocked_paths[]'` (line 39) | Step 4 |
| enforcement-config.json `colby_blocked_paths` array | mirrored in conftest.py DEFAULT_CONFIG | tests/hooks/ fixtures (test_enforce_colby_paths, test_enforce_paths) | Step 4 |
| enforce-scout-swarm.sh `roz)` case | exit code 2 with stderr message; exit 0 on pass | Eva's main-thread Agent invocation flow (pre-tool-use gate) | Step 3 |
| brain-extractor.md persona early-exit guard | agent_type whitelist (9 entries) | brain-extractor agent SubagentStop hook `if:` condition in settings.json | Step 7, Step 9 |
| SKILL.md manifest table | markdown table rows with source/destination paths | `/pipeline-setup` skill file-copy procedure | Step 8, Step 10 |
| SKILL.md settings.json JSON block | embedded JSON template | `/pipeline-setup` skill settings.json merge procedure | Step 9 |
| session-hydrate.sh source file (no-op) | exit 0, no output | Step 3a copies to .claude/hooks/; Step 0c ensures no settings.json registration | Step 10 |

## Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| session-boot.sh CORE_AGENTS list | space-separated string | For-loop on line 115 counting custom agents | Step 2 (same file) |
| session-boot.sh STATUS_JSON grep | captured regex output | jq invocation on lines 45-46 | Step 1 (same file) |
| enforce-scout-swarm.sh `check_block_content()` | bash function returning 0/1 | new roz case added in Step 3 | Step 3 (same file) |
| `.github/` path prefix | new array element | enforce-colby-paths.sh existing blocker loop (unchanged) | Step 4 |
| brain-extractor 9-agent whitelist | markdown list | SKILL.md settings.json `if:` condition | Step 7 -> Step 9 |
| enforce-scout-swarm.sh filename | manifest row | SKILL.md settings.json Agent matcher entry | Step 8 -> Step 9 |
| Step 0c cleanup instructions | markdown section | `/pipeline-setup` skill at install time | Step 10 (self-contained) |

No orphan producers. Every new producer has at least one consumer in
the same or an earlier step.

## Data Sensitivity

N/A — no data storage methods, no auth boundaries, no PII. All changes are
to enforcement scripts and install-time templates. No `public-safe` /
`auth-only` tagging applies.

## Risk

**Risk 1: SKILL.md JSON corruption (Wave 2 surgical edit SPOF).**
- Impact: every fresh `/pipeline-setup` install fails at hook registration.
- Mitigation: T-0033-020 parses the JSON block programmatically. T-0033-021
  asserts the exact hook entries exist. Both tests must pass before Wave 2
  is marked PASS. Roz runs these tests before any Ellis commit on Wave 2.
- Rollback: `git revert` the Wave 2 commit. Wave 1 changes are independent
  and stay landed. Rollback window: one commit.

**Risk 2: Dual session-boot.sh location (source/shared vs source/claude).**
- Impact: if only one is patched, the other drifts. If they're used by
  different install paths (unverified), the bug half-fixes.
- Mitigation: T-0033-002 asserts byte-identical via SHA-256. Any future
  divergence breaks the test. Both files patched in Step 1 and Step 2.
- Rollback: same as above.

**Risk 3: Narrowing prompt-brain-prefetch.sh scope affects Agatha's brain
usage.**
- Impact: Agatha no longer gets an Eva-side reminder to call `agent_search`.
  Existing Agatha captures still work (brain-extractor still fires on
  agatha SubagentStop).
- Mitigation: Agatha's persona DoR already instructs "check brain context
  first" per agent-system.md; the prefetch hook was advisory only.
- Rollback: revert the prompt-brain-prefetch.sh case statement.

**Risk 4: brain-extractor cost increase from 9-agent scope.**
- Impact: more haiku invocations per pipeline — cost increase proportional
  to the number of agents run per pipeline. Bounded: 1 extractor call per
  parent agent SubagentStop.
- Mitigation: brain-extractor uses `model: haiku` (cheapest tier). Infinite
  loop prevention preserved (brain-extractor excluded from its own trigger
  list).
- Rollback: revert Step 7 and Step 9 Edit B.

**Risk 5: Existing installs miss the new hook registration until they
re-run /pipeline-setup.**
- Impact: existing self-hosted atelier-pipeline projects continue to run
  without `enforce-scout-swarm.sh` registered. Scout protocol remains
  behavioral-only for them.
- Mitigation: this is by design — `.claude/` is regenerated by
  `/pipeline-setup`, not auto-migrated. DoD handoff note tells the user
  to re-run `/pipeline-setup` after the commit lands. Atelier-pipeline's
  own `.claude/` is re-synced in a follow-up pipeline, not this one.

## Notes for Colby

**Proven patterns to lean on:**

1. **PIPELINE_STATUS grep pattern.** Canonical pattern used everywhere
   except the buggy session-boot.sh: `'PIPELINE_STATUS: {[^}]*}'`. See
   `source/claude/hooks/enforce-scout-swarm.sh` line 74 as the reference.
   Copy this pattern exactly — do not freestyle the regex.

2. **Hook fail-open posture.** All session-boot and enforcement hooks
   follow retro lesson #003 (graceful degradation): never use `set -e`,
   exit 0 on unexpected input, only exit 2 on a confirmed block. Preserve
   this in the Roz case branch — the new content check must fail-open if
   `check_block_content` returns 0 for ambiguous structure.

3. **Step 0a cleanup pattern (mirror for Step 0c).** See
   `skills/pipeline-setup/SKILL.md` lines 36-56 (Step 0) and lines 58-65
   (Step 0b). The pattern:
   - "Unconditionally run this cleanup on every /pipeline-setup invocation.
     Silent unless it finds something to remove."
   - Numbered steps (check file, parse JSON, remove entry, write back,
     print notice).
   - "Edge case handling" subsection (Step 0 has one, Step 0b doesn't —
     Step 0c should have one minimal subsection).
   - Final "silent no-op" rule.
   - Print exact notice string specification.

4. **JSON surgical edits inside markdown fences.** Use `Edit` tool with
   a unique old_string containing enough context to be unambiguous. For
   the `"hooks": [...]` array on line 354, the unique anchor is the full
   line starting with `"hooks": [{"type": "command"` and the prompt
   `"if":` condition text. Do not include the markdown fence markers in
   old_string.

5. **brain-extractor infinite loop prevention (ADR-0024).** The
   brain-extractor agent type is deliberately excluded from its own
   SubagentStop trigger condition. When extending the agent list in
   Step 9 Edit B, do NOT add `agent_type == 'brain-extractor'`. The
   persona early-exit guard in Step 7 also keeps it off the target list.

6. **conftest.py mirror drift.** `tests/hooks/conftest.py` DEFAULT_CONFIG
   mirrors `enforcement-config.json`. Any time you edit one, edit the
   other. This is an existing fragility — future ADR could fold them.
   For now, maintain the mirror in Step 4.

**Step sizing gates (S1-S5):**
- S1 (files): Wave 1 max step = 3 files (Step 5 has 4 files, all 1-line
  edits, demoted to haiku-style mechanical work — justified). Wave 2 max
  = 1 file (SKILL.md). PASS.
- S2 (purpose): every step has one clearly named purpose. PASS.
- S3 (tests): every step has at least one test ID. PASS.
- S4 (rollback): every step reverts independently (they share no
  producer/consumer coupling outside the same step). PASS.
- S5 (complexity): no step exceeds complexity score 2. PASS.

**Test run order for Roz:**
1. Wave 1: run `pytest tests/hooks/test_session_boot*.py
   tests/hooks/test_enforce_scout_swarm.py
   tests/hooks/test_enforce_colby_paths.py
   tests/hooks/test_enforce_cal_paths.py
   tests/hooks/test_enforce_roz_paths.py
   tests/hooks/test_post_compact_reinject.py
   tests/hooks/test_prompt_brain_prefetch.py
   tests/hooks/test_brain_extractor.py`
2. Wave 2: run `pytest tests/hooks/test_pipeline_setup_skill.py` plus
   full `pytest tests/ && cd brain && node --test ../tests/brain/*.test.mjs`
   once to confirm no collateral damage.

**Files Colby must NOT touch (mechanical enforcement will block):**
- Anything under `.claude/` — `/pipeline-setup` is the only way to sync
  installed copies.
- Anything under `docs/` (except `docs/architecture/` via Cal — that's
  this ADR, already written).
- Anything under `.github/` (new blocker added in Step 4; takes effect
  after Wave 1 lands).

## DoR

| Source | Requirement | Satisfied? |
|--------|-------------|-----------|
| Research brief (C1) | session-boot.sh grep pattern mismatch (no space vs space) | Yes — Step 1 |
| Research brief (C2) | enforce-scout-swarm.sh missing from SKILL.md manifest AND settings.json | Yes — Step 8 + Step 9 |
| Research brief (M1) | colby_blocked_paths missing .github/ | Yes — Step 4 |
| Research brief (M2) | CORE_AGENTS list missing 6 agents | Yes — Step 2 |
| Research brief (M3) | Roz evidence block not content-validated | Yes — Step 3 |
| Research brief (M4) | session-hydrate.sh manifest description wrong + missing Step 0c cleanup | Yes — Step 10 |
| Research brief (m1) | enforce-roz-paths.sh header comment | Yes — Step 5 |
| Research brief (m2) | enforce-cal-paths.sh dead MultiEdit branch | Yes — Step 5 |
| Research brief (m3) | post-compact-reinject.sh brain reminder wording | Yes — Step 5 |
| Research brief (m4) | prompt-brain-prefetch.sh scope too broad | Yes — Step 6 |
| Research brief (m5) | brain-extractor.frontmatter.yml dated model alias | Yes — Step 5 |
| Research brief (G1) | brain-extractor coverage extension | Yes — Step 7 (persona) + Step 9 Edit B (settings.json) |
| Research brief (G2) | same file as m4 | Yes — Step 6 (already covered) |
| Retro risks | Retro lesson #003 (graceful degradation) — preserved in all hook edits | Yes — constraint documented in Notes for Colby item 2 |
| Project rule | Colby edits source/ only, never .claude/ | Yes — constraint stated in ADR Context and Notes for Colby |
| Project rule | All new tests pytest in tests/hooks/ | Yes — all 30 test IDs land in tests/hooks/ |

## DoD

Verification table. No silent drops.

| Acceptance check | Owner | Verification |
|------------------|-------|-------------|
| All 30 test IDs (T-0033-001 through T-0033-030) pass | Roz | `pytest tests/hooks/` exit 0 |
| Full test suite passes | Roz | `pytest tests/ && cd brain && node --test ../tests/brain/*.test.mjs` exit 0 |
| session-boot.sh byte-identical across both source trees | Roz | T-0033-002 SHA-256 check |
| SKILL.md JSON block parses as valid JSON | Roz | T-0033-020 json.loads() succeeds |
| Fresh `/pipeline-setup` produces a .claude/settings.json that registers all 4 Agent-matcher hooks (including enforce-scout-swarm.sh) | User verification after commit lands | Manual /pipeline-setup dry-run on a clean scratch directory, inspect resulting settings.json |
| No `.claude/` file was edited during Wave 1 or Wave 2 | Ellis | `git diff --name-only` shows no `.claude/` paths in either wave commit |
| brain-extractor persona early-exit guard lists 9 agent types | Roz | T-0033-018 |
| enforcement-config.json and conftest.py colby_blocked_paths match | Roz | T-0033-030 |
| DoD handoff note to user: "Existing installs need to re-run `/pipeline-setup` to pick up the enforce-scout-swarm.sh registration and the session-hydrate.sh cleanup." | Eva | present in final pipeline report |

**Handoff:** ADR saved to
`/Users/sfeirr/projects/atelier-pipeline/docs/architecture/ADR-0033-hook-enforcement-audit-fixes.md`.
10 implementation steps across 2 waves. 30 total tests. Next: Roz reviews
the test spec.
