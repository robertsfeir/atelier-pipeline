# ADR-0007: SubagentStop Warning Hook for DoR/DoD Compliance Checking

## DoR: Requirements Extracted

**Sources:** Eva invocation prompt (task + constraints), context-brief.md (user decisions), retro-lessons.md (lesson #003), Claude Code hooks documentation (code.claude.com/docs/en/hooks), existing hooks (source/hooks/enforce-*.sh), dor-dod.md (DoR/DoD format spec), SKILL.md (installation manifest), .claude/settings.json (hook registration)

| # | Requirement | Source | Citation |
|---|-------------|--------|----------|
| 1 | Hook fires on SubagentStop event | Task constraints | "The hook fires on SubagentStop event" |
| 2 | Hook reads `agent_type` from hook input; only inspects Colby and Roz output | Task constraints | "reads agent_type from hook input, only inspects colby and roz output" |
| 3 | Exit 0 ALWAYS -- warning goes to stderr, never exit 2 | Task constraints + context-brief.md | "Exit 0 ALWAYS -- warning goes to stderr, never exit 2"; context-brief: "Hooks must warn, not block" |
| 4 | Grep for `## DoR` and `## DoD` (case-insensitive, allow suffixes) | Task constraints | "Grep for '## DoR' and '## DoD' (case-insensitive, allow suffixes like '## DoR: Requirements Extracted')" |
| 5 | Handle case where agent output is not available in hook input | Task constraints | "Must handle: agent output not available in hook input" |
| 6 | Follow existing hook patterns (set -euo pipefail, jq parsing, config loading) | Task constraints | "Follow existing hook patterns from enforce-paths.sh and enforce-sequencing.sh" |
| 7 | Register as SubagentStop hook in settings.json template | Task constraints | "Register as SubagentStop hook in settings.json template" |
| 8 | Add to pipeline-setup SKILL.md installation manifest | Task constraints | "Add to pipeline-setup SKILL.md installation manifest" |
| 9 | Single ADR step -- Small feature | Task constraints | "Single ADR step -- this is a Small feature" |
| 10 | Shell script command hook type | Task context | "Shell script command hook, not agent or prompt hook type" |
| 11 | DoR format is `## DoR: Requirements Extracted` per dor-dod.md | source/references/dor-dod.md:36 | "## DoR: Requirements Extracted" |
| 12 | DoD format is `## DoD: Verification` per dor-dod.md | source/references/dor-dod.md:47 | "## DoD: Verification" |
| 13 | `last_assistant_message` field contains subagent final response text | Claude Code hooks docs | SubagentStop input schema: `last_assistant_message` (string) |
| 14 | `agent_type` field contains the subagent's frontmatter name | Claude Code hooks docs + existing hook patterns | enforce-paths.sh line 22: `AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // empty')` |

**Retro risks:**
- **Lesson #003 (Stop Hook Race Condition):** Directly relevant. The prior quality-gate Stop hook caused infinite loops by blocking subagent completion (exit 2 -> retry -> stop -> blocked). This hook MUST exit 0 always. The decision field in SubagentStop output can return `"block"` to prevent the subagent from stopping, which would replicate the exact failure mode. This hook must never output a decision JSON block.
- **Lesson #004 (Hung Process Retry Loop):** Tangentially relevant. If the hook were to block (which it must not), subagents could enter a retry loop. Exit 0 avoidance prevents this.

**Spec challenge:** The spec assumes `last_assistant_message` contains the full subagent output including DoR/DoD sections. If Claude Code truncates this field (e.g., only includes the final paragraph, or strips markdown structure), the grep will never find `## DoR` / `## DoD` and the hook becomes a no-op. Mitigation: the hook handles the absence case gracefully (warns that output was not available for inspection rather than silently passing). The Claude Code documentation describes it as "Text content of the subagent's final response" -- for subagents that produce structured output, the "final response" is typically the complete last assistant message which contains the full DoR-through-DoD structure. **Are we confident?** Moderately -- the field exists and is documented, but truncation behavior at extreme lengths is unverified. The graceful degradation (warn on absence) makes this safe regardless.

**SPOF:** The `last_assistant_message` field. If it is empty, null, or truncated for any agent invocation, the hook cannot inspect output. **Failure mode:** Hook always takes the "output not available" path -- either silently exits (if configured conservatively) or always warns "could not inspect" (noisy). **Graceful degradation:** The hook warns on stderr that output was not available for DoR/DoD inspection. Eva and pipeline agents remain the primary enforcement mechanism for DoR/DoD compliance. The hook is a safety net, not the single quality gate. This degradation is acceptable.

**Anti-goals:**

1. **Anti-goal: Blocking subagent completion.** Reason: Retro lesson #003 proved that Stop/SubagentStop hooks that exit 2 or return `decision: "block"` cause infinite loops. The hook exits 0 unconditionally. Revisit: Never. This is a permanent design constraint.

2. **Anti-goal: Inspecting all agent types.** Reason: Only Colby and Roz have DoR/DoD as a structural output requirement. Cal writes ADRs (which contain DoR/DoD but in ADR format), Ellis writes commit messages, Agatha writes docs, Poirot writes findings. Scoping to Colby+Roz keeps the hook focused. Revisit: If other agents adopt DoR/DoD as mandatory output structure.

3. **Anti-goal: Enforcing DoR/DoD content quality.** Reason: The hook checks for structural presence (`## DoR` and `## DoD` headers), not whether the tables are populated, requirements are extracted, or evidence is provided. Content quality is Eva's DoR/DoD gate and Roz's QA verification responsibility. Revisit: If a pattern emerges where agents include empty DoR/DoD sections to satisfy the hook.

---

## Status

Proposed

## Context

The DoR/DoD framework (source/references/dor-dod.md) requires every agent to produce a DoR section first and a DoD section last in their output. Eva verifies both at phase transitions (pipeline-orchestration.md, "DoR/DoD gate" protocol). However, brain context confirms: "Behavioral-only constraints in agent personas are consistently ignored by LLMs. The fix: mechanical hooks."

Currently, DoR/DoD compliance has no mechanical enforcement. Eva's spot-check is behavioral -- she reads agent output and checks for sections, but this depends on Eva's own compliance with the verification protocol. There is no hook-level safety net.

The prior attempt at a Stop hook (retro lesson #003) caused infinite loops because it exited 2 (blocking) and fired on every conversation stop including subagent completions. That hook was removed entirely. This new hook avoids that failure mode by:

1. Using SubagentStop (not Stop) -- fires only when subagents complete, not on main thread stops
2. Exiting 0 unconditionally -- warning on stderr, never blocking
3. Scoping to Colby and Roz only -- the two agents with strict DoR/DoD structural requirements
4. Never outputting a `decision` JSON block -- preventing the "block subagent from stopping" path

The SubagentStop hook receives `agent_type` (the subagent's frontmatter name) and `last_assistant_message` (the subagent's final response text) as input fields, which provide everything needed to check for DoR/DoD section headers.

### Blast Radius

**Files created:**
- `source/hooks/warn-dor-dod.sh` -- new hook script

**Files modified:**
- `.claude/settings.json` -- add SubagentStop hook registration
- `skills/pipeline-setup/SKILL.md` -- add hook to installation manifest (Step 3a table + file counts)
- `docs/guide/technical-reference.md` -- add hook to enforcement hooks documentation table
- `docs/guide/user-guide.md` -- mention in hooks section (if enforcement hooks are documented there)

**Files NOT modified (installed copies -- updated by pipeline-setup on next install):**
- `.claude/hooks/warn-dor-dod.sh` -- created during pipeline-setup, not directly

**No database, shared state, or cross-service contracts affected.** Migration/rollback section skipped per ADR template rules for stateless code changes.

**Consumers of settings.json hooks section:**
- `skills/pipeline-setup/SKILL.md` (Step 3a: documents hook registration format)
- `docs/guide/technical-reference.md` (documents hook registration)
- `.claude/settings.json` (installed copy in this project)

**Consumers of SKILL.md installation manifest:**
- Pipeline-setup skill (reads manifest to know what to install)
- `docs/guide/technical-reference.md` (documents installed files)
- `docs/guide/user-guide.md` (references hook count)

## Decision

Add a SubagentStop command hook (`source/hooks/warn-dor-dod.sh`) that inspects Colby and Roz output for DoR/DoD section headers. The hook warns on stderr when sections are missing. It exits 0 unconditionally -- never blocks, never outputs a decision JSON block.

### Hook Logic

```
1. Read JSON input from stdin
2. Check jq availability -- if missing, exit 0 (match existing pattern)
3. Extract agent_type -- if not "colby" or "roz", exit 0
4. Extract last_assistant_message -- if empty/null, warn "output not available for DoR/DoD inspection" on stderr, exit 0
5. Case-insensitive grep for "## DoR" in last_assistant_message
   - Missing: warn "WARNING: [agent_type] output missing DoR section" on stderr
6. Case-insensitive grep for "## DoD" in last_assistant_message
   - Missing: warn "WARNING: [agent_type] output missing DoD section" on stderr
7. Exit 0
```

### Registration

Register in `.claude/settings.json` under a new `SubagentStop` key (separate from `PreToolUse`):

```json
{
  "hooks": {
    "PreToolUse": [ ... existing ... ],
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/warn-dor-dod.sh"
          }
        ]
      }
    ]
  }
}
```

Note: SubagentStop hooks do not use a `matcher` field -- they fire on all subagent completions. Agent-type filtering is done inside the script.

## Alternatives Considered

### Alternative A: PreToolUse hook on Agent tool (inspect invocation, not output)

Check that Eva's invocation prompt includes DoR/DoD instructions in the `<output>` tag before the subagent runs, rather than checking the subagent's output after it runs.

**Pros:** Fires before the subagent runs, so Eva gets the warning before wasting tokens. Does not depend on `last_assistant_message` field availability.

**Cons:** Checking the invocation prompt proves Eva asked for DoR/DoD, not that the agent produced it. The whole point is catching agents that ignore behavioral instructions. Also, Eva's invocation template already includes DoR/DoD in constraints -- the gap is agent compliance, not Eva compliance.

**Rejected because:** It solves the wrong problem. The value is in catching agents that skip DoR/DoD despite being asked, not in verifying that Eva asked.

### Alternative B: Stop hook on main thread (inspect Eva's post-agent analysis)

Use a Stop hook to check Eva's own output for DoR/DoD verification language after she reads agent output.

**Pros:** Catches Eva skipping the DoR/DoD spot-check gate.

**Cons:** Replicates the exact failure mode from retro lesson #003 -- Stop hooks fire on every main thread stop, including mid-conversation responses. Grep-matching Eva's own prose for "DoR" and "DoD" would produce false positives constantly (Eva discusses DoR/DoD in routing announcements, delegation contracts, etc.).

**Rejected because:** High false-positive rate + retro lesson #003 risk. The SubagentStop approach is more precise: it fires once per subagent completion and inspects the agent's structured output, not Eva's conversational prose.

### Alternative C: Do nothing (rely on behavioral enforcement only)

Eva's DoR/DoD gate in pipeline-orchestration.md already requires spot-checking. Brain context captures compliance patterns over time.

**Pros:** Zero implementation effort. No hook maintenance.

**Cons:** Brain context explicitly states behavioral constraints are consistently ignored. Eva herself is an LLM subject to the same compliance drift. No mechanical safety net exists.

**Rejected because:** The project's core principle is "mechanical enforcement via hooks, not behavioral guidance alone" (MEMORY.md: feedback_mechanical_enforcement.md). Relying solely on behavioral enforcement contradicts the project's own design philosophy.

## Consequences

**Positive:**
- Mechanical safety net for DoR/DoD compliance on the two most-invoked build agents
- Zero risk of infinite loops or blocking (exit 0 unconditional, no decision output)
- Consistent with existing hook patterns -- same structure, same jq dependency, same graceful degradation
- Warning appears in Eva's context on stderr, giving her a signal to re-invoke or flag the gap

**Negative:**
- Warning is advisory only -- Eva (another LLM) must act on it. If Eva ignores stderr warnings, the hook has no effect. This is acceptable because the alternative (blocking) is proven dangerous.
- `last_assistant_message` truncation or absence makes the hook a no-op for that invocation. Degradation is graceful (warns about unavailability) but the check is lost.
- Adds a fourth hook script to the installation manifest, increasing setup complexity marginally (38 -> 39 mandatory files, hook count 4 -> 5 including config).

**Neutral:**
- Does not affect existing PreToolUse hooks or their behavior
- Does not require changes to agent persona files or the DoR/DoD framework itself
- Hook count in installation summary messaging needs updating

---

## Implementation Plan

### Step 1: Create warn-dor-dod.sh hook script, register in settings.json, update SKILL.md manifest

**Files to create:**
- `source/hooks/warn-dor-dod.sh` -- SubagentStop warning hook

**Files to modify:**
- `.claude/settings.json` -- add `SubagentStop` hook section
- `skills/pipeline-setup/SKILL.md` -- add hook to Step 3a manifest table, update file counts in Steps 3a, 6

**Script structure (warn-dor-dod.sh):**
```
#!/bin/bash
# DoR/DoD compliance warning hook
# SubagentStop hook -- fires when any subagent completes
#
# Checks Colby and Roz output for ## DoR and ## DoD section headers.
# Warns on stderr when missing. NEVER blocks (exit 0 always).
# This is a safety net -- Eva's DoR/DoD gate is the primary enforcement.

set -euo pipefail

INPUT=$(cat)

# Graceful degradation: no jq -> no inspection
if ! command -v jq &>/dev/null; then
  exit 0
fi

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // empty')

# Only inspect Colby and Roz output
case "$AGENT_TYPE" in
  colby|roz) ;;
  *) exit 0 ;;
esac

OUTPUT=$(echo "$INPUT" | jq -r '.last_assistant_message // empty')

# Handle missing output
if [ -z "$OUTPUT" ]; then
  echo "WARNING: $AGENT_TYPE completed but output not available for DoR/DoD inspection." >&2
  exit 0
fi

# Case-insensitive check for DoR section header (allows suffixes like "## DoR: Requirements Extracted")
if ! echo "$OUTPUT" | grep -qi "^## DoR"; then
  echo "WARNING: $AGENT_TYPE output missing '## DoR' section. DoR/DoD framework requires DoR as the first output section." >&2
fi

# Case-insensitive check for DoD section header (allows suffixes like "## DoD: Verification")
if ! echo "$OUTPUT" | grep -qi "^## DoD"; then
  echo "WARNING: $AGENT_TYPE output missing '## DoD' section. DoR/DoD framework requires DoD as the last output section." >&2
fi

exit 0
```

**settings.json addition:**
```json
"SubagentStop": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/warn-dor-dod.sh"
      }
    ]
  }
]
```

**SKILL.md changes:**
- Step 3a table: add row `source/hooks/warn-dor-dod.sh` | `.claude/hooks/warn-dor-dod.sh` | Warns when Colby/Roz output missing DoR/DoD sections
- Step 3a settings.json example: add `SubagentStop` section
- Step 3a file count: "4 files" -> "5 files" (4 scripts + 1 config)
- Step 6 summary: update hook count from 4 to 5, total mandatory files from 38 to 39
- Step 6 hooks directory line: update "4 files" to "5 files" and add description

**Acceptance criteria:**
1. `source/hooks/warn-dor-dod.sh` exists, is well-formed bash, follows existing hook patterns (set -euo pipefail, jq check, INPUT=$(cat), agent_type extraction)
2. Script exits 0 in every code path -- no exit 2, no decision JSON output
3. Script only inspects agent_type "colby" or "roz" -- all others exit 0 immediately
4. Script greps case-insensitively for `^## DoR` and `^## DoD` in `last_assistant_message`
5. Script warns on stderr when sections are missing, warns when output is unavailable
6. `.claude/settings.json` has a `SubagentStop` section registering the hook
7. `skills/pipeline-setup/SKILL.md` Step 3a includes the hook in the manifest table
8. SKILL.md file counts are updated consistently (39 mandatory files, 5 hook files)
9. Script does not read any files from disk (no config loading needed -- this hook is self-contained)

**Estimated complexity:** Low. Single script file following established patterns, two file modifications.

---

## Comprehensive Test Specification

### Step 1 Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0007-001 | Happy | Colby output with both `## DoR` and `## DoD` headers: hook exits 0, no stderr output |
| T-0007-002 | Happy | Roz output with both `## DoR: Requirements Extracted` and `## DoD: Verification` (with suffixes): hook exits 0, no stderr output |
| T-0007-003 | Happy | Non-Colby/Roz agent (e.g., `agent_type: "ellis"`): hook exits 0 immediately, no stderr |
| T-0007-004 | Happy | Empty `agent_type` (main thread stop leaked to SubagentStop): hook exits 0, no stderr |
| T-0007-005 | Failure | Colby output missing `## DoR`: hook exits 0, stderr contains "WARNING: colby output missing '## DoR' section" |
| T-0007-006 | Failure | Colby output missing `## DoD`: hook exits 0, stderr contains "WARNING: colby output missing '## DoD' section" |
| T-0007-007 | Failure | Roz output missing both `## DoR` and `## DoD`: hook exits 0, stderr contains both warnings |
| T-0007-008 | Failure | Colby output is empty string (`last_assistant_message: ""`): hook exits 0, stderr contains "output not available for DoR/DoD inspection" |
| T-0007-009 | Failure | `last_assistant_message` field is null/missing from input JSON: hook exits 0, stderr contains "output not available" warning |
| T-0007-010 | Boundary | `## DoR` appears mid-line (not at line start, e.g., "See ## DoR above"): should NOT match (grep `^## DoR` requires line start) |
| T-0007-011 | Boundary | Mixed case `## dor` and `## dod` (all lowercase): hook matches (case-insensitive grep) and does NOT warn |
| T-0007-012 | Boundary | `## DOR` and `## DOD` (all uppercase): hook matches and does NOT warn |
| T-0007-013 | Boundary | `## DoR` present but `## DoD` absent: hook warns only about DoD, not DoR |
| T-0007-014 | Boundary | Agent type is "Colby" (capitalized, not matching frontmatter convention "colby"): hook exits 0 without inspection (case-sensitive agent_type match) |
| T-0007-015 | Error | jq not installed: hook exits 0 silently (graceful degradation) |
| T-0007-016 | Error | Malformed JSON input (not valid JSON): hook exits 0 (set -euo pipefail catches jq error, but jq with `// empty` returns empty on parse failure -- verify behavior) |
| T-0007-017 | Regression | Hook NEVER exits with code 2 regardless of input (fuzz: empty input, garbage input, huge input) -- regression guard against retro lesson #003 |
| T-0007-018 | Regression | Hook stdout is empty in all test cases (no decision JSON output -- prevents SubagentStop block behavior) |
| T-0007-019 | Security | Input with shell metacharacters in `last_assistant_message` (e.g., `$(rm -rf /)`, backticks): hook does not execute injected commands (jq -r outputs literal text, echo + grep pipe is safe) |
| T-0007-020 | Happy | `agent_type: "cal"` with output missing DoR/DoD: hook exits 0, no warnings (cal is not inspected) |
| T-0007-021 | Happy | `agent_type: "agatha"` with output missing DoR/DoD: hook exits 0, no warnings |

### Step 1 Telemetry

Telemetry: stderr warning message `"WARNING: {agent_type} output missing '## DoR' section"` or `"WARNING: {agent_type} output missing '## DoD' section"`. Trigger: when a Colby or Roz subagent completes without the corresponding section header. Absence means: either all Colby/Roz invocations include DoR/DoD (ideal), or the hook is not firing (check settings.json registration).

Telemetry: stderr warning `"WARNING: {agent_type} completed but output not available for DoR/DoD inspection"`. Trigger: when `last_assistant_message` is empty/null for a Colby or Roz completion. Absence means: `last_assistant_message` is reliably populated by Claude Code for these agent types.

### Contract Boundaries

| Producer | Consumer | Expected Shape |
|----------|----------|----------------|
| Claude Code SubagentStop event | `warn-dor-dod.sh` | JSON with `agent_type` (string), `last_assistant_message` (string, may be empty/null) |
| `warn-dor-dod.sh` stderr | Eva (main thread) | Human-readable warning text prefixed with "WARNING:" |
| `warn-dor-dod.sh` stdout | Claude Code SubagentStop handler | Empty (no output). Any JSON on stdout would be interpreted as a decision block -- must be empty. |
| `warn-dor-dod.sh` exit code | Claude Code | Always 0. Exit 2 would block the tool call (SubagentStop decision semantics). |

---

## Notes for Colby

1. **Follow enforce-paths.sh as the structural template.** Same preamble: `set -euo pipefail`, `INPUT=$(cat)`, jq availability check, agent_type extraction via `jq -r '.agent_type // empty'`. The main difference: this hook reads `last_assistant_message` instead of `tool_input.file_path`, and this hook never loads enforcement-config.json (it is self-contained).

2. **The `^` anchor in grep matters.** `grep -qi "^## DoR"` matches `## DoR` only at the start of a line. The `last_assistant_message` is a multi-line string -- `echo "$OUTPUT" | grep` will check each line. Without `^`, `## DoR` appearing inside prose (e.g., "the ## DoR section was...") would match. With `^`, only actual markdown headers match. This is the correct behavior per the DoR/DoD framework, which specifies these as H2 headers.

3. **Never write to stdout.** SubagentStop hooks interpret stdout JSON as a decision block. `{"decision": "block", "reason": "..."}` on stdout would prevent the subagent from completing -- recreating retro lesson #003. All messaging goes to stderr. If in doubt, redirect: `echo "..." >&2`.

4. **The `set -euo pipefail` + jq failure interaction.** When jq receives malformed JSON, `jq -r '.agent_type // empty'` returns empty string and exits 0 (the `// empty` fallback handles it). However, if the pipe itself fails (e.g., `echo` to a broken pipe), `pipefail` could cause a non-zero exit. The `|| empty` pattern in jq handles most cases. Test T-0007-016 covers this edge.

5. **No chmod in the source template.** The SKILL.md Step 3a already has `chmod +x .claude/hooks/*.sh` which covers all `.sh` files in the hooks directory. No additional chmod instruction needed.

6. **SKILL.md edits are in three locations.** (a) Step 3a manifest table: add one row. (b) Step 3a settings.json example: add the SubagentStop section. (c) Step 6 summary: update three numbers (hook file count 4->5, total mandatory files 38->39, hooks directory line). Search for "38" and "4 files" to find all instances. Also update the "Total with hooks" line in Step 3a from 38 to 39.

7. **Brain context confirms SubagentStop fires separately from Stop.** The hook will not fire on Eva's main thread stops. It fires once per subagent completion. This is fundamentally different from the removed quality-gate Stop hook which fired on every conversation stop.

8. **settings.json: the installed copy in `.claude/settings.json` is what this project uses.** Edit that file directly for this project. The `source/` directory does not have a settings.json template -- settings.json is project-specific and assembled during pipeline-setup. The SKILL.md documents what the setup skill writes, but the actual registration for THIS project goes in `.claude/settings.json`.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | Hook fires on SubagentStop event | Covered | settings.json registration under `SubagentStop` key; tests T-0007-001 through T-0007-004 |
| 2 | Only inspects Colby and Roz output | Covered | `case "$AGENT_TYPE" in colby|roz)` filter; tests T-0007-003, T-0007-004, T-0007-014, T-0007-020, T-0007-021 |
| 3 | Exit 0 always, never exit 2 | Covered | Every code path ends with `exit 0`; tests T-0007-017, T-0007-018 (regression guards) |
| 4 | Grep for `## DoR` and `## DoD` case-insensitive with suffix support | Covered | `grep -qi "^## DoR"` / `grep -qi "^## DoD"`; tests T-0007-001, T-0007-002, T-0007-011, T-0007-012 |
| 5 | Handle missing agent output | Covered | Empty/null check on `$OUTPUT`; tests T-0007-008, T-0007-009 |
| 6 | Follow existing hook patterns | Covered | Same preamble, jq check, input parsing as enforce-paths.sh; test T-0007-015 |
| 7 | Register in settings.json | Covered | Step 1 acceptance criteria #6 |
| 8 | Add to SKILL.md manifest | Covered | Step 1 acceptance criteria #7, #8; Notes for Colby #6 |
| 9 | Single ADR step | Covered | One implementation step with all changes grouped |
| 10 | Shell script command hook type | Covered | `"type": "command"` in settings.json registration |
| 11 | DoR format per dor-dod.md | Covered | Grep pattern matches `## DoR` prefix allowing `: Requirements Extracted` suffix |
| 12 | DoD format per dor-dod.md | Covered | Grep pattern matches `## DoD` prefix allowing `: Verification` suffix |
| 13 | `last_assistant_message` used for inspection | Covered | Script extracts via `jq -r '.last_assistant_message // empty'` |
| 14 | `agent_type` used for filtering | Covered | Script extracts via `jq -r '.agent_type // empty'` |

**Architectural decisions not in the spec:**
- `^` anchor on grep to require line-start position (prevents false matches in prose)
- No config file dependency (hook is self-contained, unlike enforce-paths.sh which reads enforcement-config.json)
- Case-sensitive agent_type matching (frontmatter names are lowercase by convention; "Colby" would not match)

**Rejected alternatives with reasoning:**
- PreToolUse on Agent invocation (inspects input, not output -- solves wrong problem)
- Stop hook on main thread (retro lesson #003 risk + high false-positive rate)
- Do nothing (contradicts project's mechanical enforcement principle)

**Technical constraints discovered:**
- SubagentStop hooks interpret stdout JSON as decision blocks -- stdout must remain empty to avoid accidentally blocking subagent completion
- SubagentStop has no `matcher` field -- all subagent completions trigger the hook, so agent-type filtering must be inside the script
- `last_assistant_message` may be empty/null -- the hook must handle this gracefully rather than failing on the jq extraction
