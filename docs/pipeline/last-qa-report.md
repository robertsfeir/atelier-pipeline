# QA Report -- 2026-03-29 (ADR-0009)
*Reviewed by Roz*

PIPELINE_STATUS: {"roz_qa": "PASS"}

## DoR: Requirements Extracted

| # | Requirement | Source |
|---|-------------|--------|
| R1 | Sentinel is optional 10th agent, user opts in during /pipeline-setup | ADR-0009 |
| R2 | Full install chain: pip check, semgrep-mcp install, persona copy, MCP register, config flag | ADR-0009 |
| R3 | Semgrep MCP backbone: `semgrep_scan`, `semgrep_findings`, `security_check` | ADR-0009 |
| R4 | Runs at review juncture parallel with Roz, Poirot, Robert, Sable | ADR-0009 |
| R5 | Read-only: `disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit` | ADR-0009 |
| R6 | Security BLOCKER = pipeline halt | ADR-0009 |
| R7 | `pipeline-config.json` gets `sentinel_enabled: false` default | ADR-0009 |
| R8 | Information asymmetry: diff + scan results only, no spec/ADR/UX | ADR-0009 |
| R9 | All changes in `source/` and `skills/` only, not `.claude/` | ADR-0009 |
| R10 | XML format per `xml-prompt-schema.md` tag order | ADR-0009 |
| R11 | Triage consensus matrix updated with Sentinel column | ADR-0009 |
| R12 | Invocation template `sentinel-audit` added | ADR-0009 |
| R13 | Agent system tables updated (subagent + no-skill-tool + phase transitions) | ADR-0009 |
| R14 | Setup flow after Step 6, before brain offer | ADR-0009 |
| R15 | Persona in `source/agents/`, installed to `.claude/agents/` by setup | ADR-0009 |
| R16 | Mechanical enforcement via `enforce-paths.sh` catch-all, hook NOT modified | ADR-0009 |

### Retro Risks

| Lesson | Risk | Verified |
|--------|------|----------|
| #003 (Stop hook race) | Sentinel MCP failure could block pipeline | Mitigated: persona and orchestration docs specify graceful degradation |
| #004 (Hung process retry) | Semgrep scan could hang | Mitigated: persona `<constraints>` includes explicit "STOP, report partial, do not retry" |
| Behavioral constraints ignored (brain lesson) | Read-only relies on frontmatter alone | Mitigated: `enforce-paths.sh` catch-all confirmed unchanged, covers `sentinel` agent type |

---

### Verdict: PASS

---

## Test-by-Test Verification (55 tests)

### Step 0: Sentinel Persona File (11 tests)

| ID | Category | Status | Evidence |
|----|----------|--------|----------|
| T-0009-001 | Happy | PASS | Lines 1-8: YAML frontmatter with `name: sentinel`, description mentions Semgrep MCP and security, `disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit` |
| T-0009-002 | Happy | PASS | Lines 12-22: "You are Sentinel, the Security Audit Agent. Pronouns: they/them." + "You run on the Opus model." |
| T-0009-003 | Happy | PASS | Lines 24-42: references `.claude/references/agent-preamble.md` steps 1-5; includes scan, retrieve findings, cross-reference diff, classify severity |
| T-0009-004 | Happy | PASS | Lines 44-96: "Scan Phase" (items 1-4), "Interpret Phase" (items 5-7), "Report Phase" (items 8-9) |
| T-0009-005 | Failure | PASS | Lines 58-60: "If Semgrep MCP is unavailable...report: 'Sentinel: scan unavailable -- Semgrep MCP not responding. Manual security review recommended.' Do not crash. Do not retry." |
| T-0009-006 | Failure | PASS | Line 124: "do not read spec files, ADR files, product docs, UX docs, context-brief.md, or pipeline-state.md" |
| T-0009-007 | Failure | PASS | Line 130: "If Semgrep scan hangs or times out, STOP. Report partial results with what you have. Do not retry. Do not sleep-poll-kill-retry." |
| T-0009-008 | Happy | PASS | Lines 134-168: full output template with findings table (location, severity, category, CWE/OWASP, description, remediation) + scan metadata |
| T-0009-009 | Boundary | PASS | Lines 78-87: BLOCKER, MUST-FIX, NIT defined matching pipeline conventions |
| T-0009-010 | Regression | PASS | `git diff HEAD` shows zero changes to any of the 9 existing agent persona files |
| T-0009-011 | Happy | PASS | Tag order: identity(12) -> required-actions(24) -> workflow(44) -> examples(98) -> tools(113) -> constraints(123) -> output(134) -- matches `xml-prompt-schema.md` |

### Step 1: Pipeline Config Template (3 tests)

| ID | Category | Status | Evidence |
|----|----------|--------|----------|
| T-0009-020 | Happy | PASS | Line 10: `"sentinel_enabled": false` |
| T-0009-021 | Boundary | PASS | `jq .` parses successfully with all fields present |
| T-0009-022 | Regression | PASS | Diff shows only addition of `sentinel_enabled` field and trailing comma on `integration_branch` |

### Step 2: Agent System Tables (5 tests)

| ID | Category | Status | Evidence |
|----|----------|--------|----------|
| T-0009-030 | Happy | PASS | Line 65: Sentinel row with "Security audit -- Semgrep-backed SAST (opt-in)" and "Read, Glob, Grep, Bash (read-only) + Semgrep MCP tools" |
| T-0009-031 | Happy | PASS | Line 290: "Sentinel (security audit)" mapped to ".claude/agents/sentinel.md" |
| T-0009-032 | Happy | PASS | Line 136: review juncture includes "Sentinel (if enabled) (parallel)" |
| T-0009-033 | Regression | PASS | Diff shows only line additions; no existing rows modified |
| T-0009-034 | Happy | PASS | Subagent table: "(opt-in)"; phase transitions: "(if enabled)" |

### Step 3: Triage Consensus Matrix (7 tests)

| ID | Category | Status | Evidence |
|----|----------|--------|----------|
| T-0009-040 | Happy | PASS | Header: `\| Roz \| Poirot \| Robert \| Sable \| Sentinel \| Action \|` |
| T-0009-041 | Happy | PASS | BLOCKER row: "any + any + any + any + BLOCKER = HALT" with false positive verification step |
| T-0009-042 | Happy | PASS | "PASS + PASS + -- + -- + MUST-FIX = SECURITY CONCERN. Queue fix, Colby priority." |
| T-0009-043 | Happy | PASS | "MUST-FIX + flags issue + -- + -- + MUST-FIX = CONVERGENT SECURITY." |
| T-0009-044 | Boundary | PASS | All pre-existing rows have `--` in Sentinel column |
| T-0009-045 | Failure | PASS | "When `sentinel_enabled: false`, the Sentinel column is absent from triage" |
| T-0009-046 | Regression | PASS | All original row actions preserved; only Sentinel column added |

### Step 4: Pipeline Orchestration (6 tests)

| ID | Category | Status | Evidence |
|----|----------|--------|----------|
| T-0009-050 | Happy | PASS | Line 435: "Sentinel (security, if `sentinel_enabled: true`)" as fifth reviewer |
| T-0009-051 | Happy | PASS | Line 398: "+ Sentinel (if enabled) (parallel, triage matrix)" in flow diagram |
| T-0009-052 | Happy | PASS | Lines 129-133: Sentinel runs in parallel with Roz and Poirot per build unit when enabled |
| T-0009-053 | Failure | PASS | Lines 132-133: "If Sentinel invocation fails...Eva logs 'Sentinel audit skipped: [reason]' and proceeds. Sentinel failure is never a pipeline blocker." |
| T-0009-054 | Regression | PASS | All 12 mandatory gates retain existing behavior; gate 5 only gains appended note |
| T-0009-055 | Boundary | PASS | All mentions gated: "When `sentinel_enabled: true`", "if `sentinel_enabled: true`", "(if enabled)" |

### Step 5: Invocation Template (7 tests)

| ID | Category | Status | Evidence |
|----|----------|--------|----------|
| T-0009-060 | Happy | PASS | `<template id="sentinel-audit">` present between poirot-blind and distillator-compress |
| T-0009-061 | Happy | PASS | `<task>`: "Security audit of Colby's build output for ADR-NNNN Step N" + review juncture variant |
| T-0009-062 | Happy | PASS | All 7 constraint bullets: diff only, Semgrep tools, cross-reference, min 3 findings, CWE/OWASP, stop if hang, grep verify |
| T-0009-063 | Happy | PASS | `<output>`: "Security report with findings table...scan metadata, DoR/DoD sections" |
| T-0009-064 | Failure | PASS | No `<brain-context>` tag in sentinel-audit template |
| T-0009-065 | Failure | PASS | No `<read>` tag with spec/ADR/UX files in sentinel-audit template |
| T-0009-066 | Regression | PASS | Diff shows only sentinel-audit insertion; no existing templates modified |

### Step 6: Pipeline-Setup Opt-In (12 tests)

| ID | Category | Status | Evidence |
|----|----------|--------|----------|
| T-0009-070 | Happy | PASS | Step 6a at line 337; brain setup offer at line 366; correct ordering |
| T-0009-071 | Happy | PASS | Prompt text mentions SAST, Semgrep, Python, pip, optional |
| T-0009-072 | Happy | PASS | Steps 1-6 in numbered order: pip check, install, copy, MCP register, config flag, summary update |
| T-0009-073 | Happy | PASS | Step 4: `"semgrep": {"command": "semgrep-mcp"}` -- flat format per MEMORY.md |
| T-0009-074 | Failure | PASS | "Skip entirely. `sentinel_enabled` remains `false`" |
| T-0009-075 | Failure | PASS | Step 1: "Sentinel requires Python and pip. Install them and re-run setup to enable Sentinel." Skip without error. |
| T-0009-076 | Happy | PASS | Both paths: "enabled (Semgrep MCP)" or "not enabled" |
| T-0009-077 | Happy | PASS | Conditional manifest table with source/destination/condition columns |
| T-0009-078 | Regression | PASS | Diff shows only insertion between Step 6 summary and brain offer; no existing lines modified |
| T-0009-079 | Boundary | PASS | Step 4 handles both: "If `.mcp.json` exists: read it, merge" and "does not exist: create it" |
| T-0009-080 | Security | PASS | Step 3: "Copy `source/agents/sentinel.md` to `.claude/agents/sentinel.md`" |

### Step 7: Model Table (3 tests)

| ID | Category | Status | Evidence |
|----|----------|--------|----------|
| T-0009-090 | Happy | PASS | `\| **Sentinel** \| Opus \| Security judgment requires strong reasoning...` |
| T-0009-091 | Happy | PASS | "Semgrep provides data; Sentinel must interpret relevance, reachability, and severity in context of the diff." |
| T-0009-092 | Regression | PASS | Single line added; no existing rows modified |

### Step 8: Pipeline Operations Update (6 tests)

| ID | Category | Status | Evidence |
|----|----------|--------|----------|
| T-0009-100 | Happy | PASS | Item 3: "AND Sentinel for security audit (if `sentinel_enabled: true`) in PARALLEL" |
| T-0009-101 | Happy | PASS | Item 4: "Findings unique to Sentinel get CWE/OWASP cross-reference." |
| T-0009-102 | Happy | PASS | Item 8: "+ Sentinel (if `sentinel_enabled: true`) in parallel" |
| T-0009-103 | Happy | PASS | Brain capture: "Eva captures Sentinel findings post-review via `agent_capture` with `source_agent: 'eva'`, `thought_type: 'insight'` (same pattern as Poirot -- Sentinel does not touch brain directly)." |
| T-0009-104 | Regression | PASS | Existing items modified only to add Sentinel references; no behavior removed |
| T-0009-105 | Boundary | PASS | Item 3 and item 8 both gated on `sentinel_enabled: true` |

---

## Cross-Cutting Verification

| Check | Status | Details |
|-------|--------|---------|
| `enforce-paths.sh` NOT modified | PASS | Zero diff on `source/hooks/enforce-paths.sh` |
| No `.claude/` files touched | PASS | Zero diff in `.claude/` directory; 9 original agents only |
| All changes in `source/` and `skills/` only (R9) | PASS | 1 new + 6 modified in `source/`, 1 modified in `skills/` |
| Conditional language on every Sentinel mention | PASS | Verified across all 7 modified files |
| XML tag order per schema | PASS | 7 tags in correct order per `xml-prompt-schema.md` |
| MCP flat format in SKILL.md | PASS | `"semgrep": {"command": "semgrep-mcp"}` |
| Valid JSON in pipeline-config.json | PASS | `jq` parses successfully |
| Unfinished markers | PASS | 0 TODO/FIXME/HACK/XXX in changed code (2 matches are instructional text) |

## Requirements Verification

| # | Requirement | Colby Claims | Roz Verified | Finding |
|---|-------------|-------------|-------------|---------|
| R1 | Sentinel optional, opts in during setup | Step 1 + Step 6 | PASS | `sentinel_enabled: false` default; Step 6a opt-in flow |
| R2 | Full install chain | Step 6 | PASS | pip check -> install -> copy -> MCP register -> config flag |
| R3 | Semgrep MCP backbone | Step 0 + Step 5 | PASS | Persona references all three Semgrep MCP tools |
| R4 | Runs at review juncture parallel | Step 4 + Step 8 | PASS | Review juncture and per-unit QA both updated |
| R5 | Read-only access | Step 0 | PASS | `disallowedTools` + hook catch-all |
| R6 | BLOCKER = halt | Step 3 | PASS | Triage matrix row present |
| R7 | Config gets sentinel_enabled | Step 1 | PASS | Field present, default false |
| R8 | Information asymmetry | Step 0 + Step 5 | PASS | Constraints + template enforce no spec/ADR/UX |
| R9 | Changes in source/ and skills/ only | All | PASS | No .claude/ or hook changes |
| R10 | XML format per schema | Step 0 | PASS | 7-tag order verified |
| R11 | Triage matrix updated | Step 3 | PASS | Sentinel column + 3 new rows + `--` on existing |
| R12 | Invocation template added | Step 5 | PASS | `sentinel-audit` template present |
| R13 | Agent system tables updated | Step 2 | PASS | Subagent + no-skill-tool + phase transitions |
| R14 | Setup after Step 6, before brain | Step 6 | PASS | Correct positioning verified |
| R15 | Persona in source/, installed by setup | Step 0 + Step 6 | PASS | File in `source/agents/`; SKILL.md copies to `.claude/agents/` |
| R16 | Mechanical enforcement via hook | Blast radius | PASS | `enforce-paths.sh` unchanged; catch-all covers sentinel |

## Unfinished Markers

`grep -r "TODO|FIXME|HACK|XXX"` across all changed files: **0 matches in changed code.** 2 matches in `invocation-templates.md` are instructional text telling agents to check for unfinished markers -- not actual unfinished work.

## Issues Found

None. No blockers. No fix-required items.

## Doc Impact: NO

All changes are to pipeline configuration templates, agent personas, and operational documentation within `source/` -- these ARE the documentation. No separate user-facing docs require updating. The SKILL.md update includes the user-facing opt-in flow.

## DoD: Verification

| ADR Requirement | Test IDs | Status |
|-----------------|----------|--------|
| R1: Optional, opts in during setup | T-0009-020, T-0009-070 through T-0009-080 | Done (13/13) |
| R2: Full install chain | T-0009-072, T-0009-073, T-0009-080 | Done (3/3) |
| R3: Semgrep MCP backbone | T-0009-003, T-0009-004, T-0009-062 | Done (3/3) |
| R4: Runs at review juncture | T-0009-050, T-0009-100 through T-0009-102 | Done (4/4) |
| R5: Read-only access | T-0009-001, T-0009-006 | Done (2/2) |
| R6: BLOCKER = halt | T-0009-041 | Done (1/1) |
| R7: Config gets sentinel_enabled | T-0009-020 through T-0009-022 | Done (3/3) |
| R8: Information asymmetry | T-0009-006, T-0009-064, T-0009-065 | Done (3/3) |
| R9: Changes in source/ and skills/ only | Cross-cutting verification | Done |
| R10: XML format per schema | T-0009-011 | Done (1/1) |
| R11: Triage matrix updated | T-0009-040 through T-0009-046 | Done (7/7) |
| R12: Invocation template added | T-0009-060 through T-0009-066 | Done (7/7) |
| R13: Agent system tables updated | T-0009-030 through T-0009-034 | Done (5/5) |
| R14: Setup after Step 6, before brain | T-0009-070, T-0009-078 | Done (2/2) |
| R15: Persona in source/, installed by setup | T-0009-001, T-0009-080 | Done (2/2) |
| R16: Mechanical enforcement via hook | Cross-cutting verification | Done |

All 16 requirements verified. 55/55 tests pass. 0 deferred items.

### Recurring QA Patterns

None identified for this ADR. The dual-tree sync gap (`.claude/` installed copies not updated) is expected per R9 and consistent with prior ADR-0008 observation.

### Roz's Assessment

Clean implementation. All 55 test specifications pass. Colby followed the ADR precisely across all 8 steps.

The persona file is well-structured, modeled correctly on `source/agents/investigator.md` (Poirot) as directed. Both retro lessons (#003 graceful degradation, #004 hung process handling) are addressed in the persona's constraints. The triage consensus matrix expansion is correctly done with `--` on existing rows and three new Sentinel-specific scenarios. Conditional language is consistent throughout -- every Sentinel mention in every file is properly gated.

The implementation is purely additive. No existing behavior is changed when `sentinel_enabled: false`. No hooks were modified. No `.claude/` installed copies were touched. The 9 existing agent personas are untouched.
