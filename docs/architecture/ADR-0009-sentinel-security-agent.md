# ADR-0009: Sentinel Security Audit Agent with Semgrep MCP -- Optional 10th Pipeline Agent

## Status

Proposed

## DoR: Requirements Extracted

| # | Requirement | Source | Notes |
|---|-------------|--------|-------|
| R1 | Sentinel is the optional 10th agent -- user opts in during `/pipeline-setup` | context-brief.md | If user declines, pipeline is unchanged |
| R2 | If opted in: install Semgrep MCP (`pip install semgrep-mcp`), copy Sentinel persona, register MCP in project `.mcp.json`, set `sentinel_enabled: true` in `pipeline-config.json` | context-brief.md | Full install chain |
| R3 | Sentinel is backed by Semgrep MCP (LGPL 2.1, pip-installable); tools: `security_check`, `semgrep_scan`, `semgrep_findings` | context-brief.md, brain-context | Semgrep MCP is the scanning backbone; Sentinel interprets results |
| R4 | Sentinel runs at review juncture in parallel with Roz, Poirot, Robert, Sable | context-brief.md | Conditional on `sentinel_enabled: true` |
| R5 | Sentinel is read-only (same access as Poirot, Robert, Sable): `disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit` | context-brief.md | Mechanically enforced by `enforce-paths.sh` catch-all |
| R6 | Security BLOCKER from Sentinel = pipeline halt (same as Roz BLOCKER) | context-brief.md | Must update triage consensus matrix |
| R7 | `pipeline-config.json` template gets `sentinel_enabled` field | context-brief.md | Default: `false` |
| R8 | Sentinel receives diff (like Poirot) + Semgrep scan results -- information asymmetry (no spec, no ADR, no UX doc) | constraints | Parallel to Poirot's design philosophy |
| R9 | All changes in `source/` and `skills/` directories only | context-brief.md, constraints | Not `.claude/` -- dual tree convention |
| R10 | Sentinel persona follows pipeline XML format (`identity`, `required-actions` with preamble reference, `workflow`, `constraints`, `output`) | constraints | Per `xml-prompt-schema.md` |
| R11 | Add Sentinel to triage consensus matrix in `pipeline-operations.md` | constraints | New column in matrix |
| R12 | Add `sentinel-audit` template to `invocation-templates.md` | constraints | Eva needs a standard invocation template |
| R13 | Add Sentinel to `agent-system.md` subagent table | constraints | Architecture and `no-skill-tool` tables |
| R14 | Opt-in flow in SKILL.md: after Step 6 summary, before brain setup offer | constraints | Check pip, install semgrep-mcp, copy persona, register MCP, set config flag |
| R15 | Agents must NEVER be in plugin's native `agents/` directory; must be installed to project `.claude/agents/` via `/pipeline-setup` | brain-context | Sentinel persona lives in `source/shared/agents/`, installed by setup |
| R16 | Behavioral constraints are consistently ignored; mechanical enforcement via hooks required | brain-context (retro lesson) | Sentinel's read-only access is enforced by `enforce-paths.sh` catch-all, not just by `disallowedTools` frontmatter |

### Retro Risks

| Lesson | Risk to this feature | Mitigation |
|--------|---------------------|------------|
| #003 (Stop hook race condition) | Adding Sentinel to review juncture adds another parallel subagent invocation; if Semgrep MCP is not installed or crashes, could block pipeline | Sentinel invocation must be conditional on `sentinel_enabled: true`; Semgrep MCP errors produce a WARN, not a HALT (graceful degradation) |
| Behavioral constraints ignored (brain lesson) | Sentinel's read-only access relies partly on `disallowedTools` frontmatter which is behavioral | Mechanical enforcement via `enforce-paths.sh` catch-all (`*` case at line 112) blocks all unknown agent types from writing. Sentinel falls into this catch-all. No hook changes needed. |
| #004 (Hung process retry loop) | Semgrep scan could hang on large repos | Sentinel persona must include explicit "if scan hangs, stop and report partial results" constraint |

## Context

The pipeline currently runs four reviewers at the review juncture: Roz (informed QA), Poirot (blind diff), Robert (spec compliance, Medium/Large), and Sable (UX compliance, Large). None of these agents perform static security analysis with dedicated tooling. Poirot checks for security issues in the diff but relies on LLM judgment without a SAST scanner.

Semgrep MCP (github.com/semgrep/mcp, LGPL 2.1) provides a native MCP server for Claude Code with static analysis capabilities. It is pip-installable (`pip install semgrep-mcp`) and exposes tools including `security_check`, `semgrep_scan`, `semgrep_scan_with_custom_rule`, `get_abstract_syntax_tree`, and `semgrep_findings`. This is the only SAST tool with native MCP integration at the time of this ADR.

The user has decided Sentinel is opt-in during `/pipeline-setup` -- projects that do not enable it see zero changes to pipeline behavior. The `pipeline-config.json` flag `sentinel_enabled` gates all Sentinel behavior.

### Spec Challenge

**The spec assumes** that Semgrep MCP tools will be available as MCP tools in the subagent's context when Sentinel is invoked. If this is wrong (because MCP tools from project-level `.mcp.json` are not available to subagents, or because Semgrep MCP server fails to start), the design fails because Sentinel cannot perform scans. **Are we confident?** Partially. MCP tools registered in `.mcp.json` are available to Claude Code's main thread and subagents. However, Semgrep MCP requires Python and pip, which may not be available in all environments. The opt-in flow validates the prerequisite (`pip` availability) before installation.

**SPOF:** The Semgrep MCP server process. **Failure mode:** If the MCP server crashes or fails to start (Python version incompatibility, pip install failure, corrupted package), Sentinel's invocation would fail entirely -- no security findings for that pipeline run. **Graceful degradation:** Eva checks `sentinel_enabled` but also wraps Sentinel invocation in error handling. If Sentinel fails, Eva logs "Sentinel security audit skipped: [reason]" and proceeds -- the pipeline is not blocked. Security findings from Sentinel are additive (the pipeline ran without them before). The user is informed so they can run Semgrep manually if desired.

## Decision

Implement Sentinel as an optional 10th agent: a Semgrep-backed security auditor that runs at the review juncture in parallel with existing reviewers. All changes are additive and gated behind `sentinel_enabled: true` in `pipeline-config.json`.

### Agent Design

Sentinel is a read-only subagent with access to Semgrep MCP tools. It operates under partial information asymmetry: it receives the git diff (like Poirot) plus the Semgrep scan results, but no spec, ADR, or UX doc. This design ensures Sentinel evaluates security independently of what the code was "intended" to do.

Sentinel's workflow:
1. Receives the diff from Eva
2. Calls Semgrep MCP tools (`semgrep_scan` on changed files, `semgrep_findings` for results)
3. Interprets findings in the context of the diff (reduces false positives from unchanged code)
4. Classifies findings: BLOCKER (exploitable vulnerability), MUST-FIX (security concern), NIT (hardening suggestion)
5. Produces a structured security report

### Pipeline Integration

- **Review juncture (Medium/Large):** Eva invokes Sentinel in parallel with Roz, Poirot, Robert, and Sable (when `sentinel_enabled: true`)
- **Per-unit QA (all sizes):** Eva invokes Sentinel in parallel with Roz and Poirot after each Colby build unit (when `sentinel_enabled: true`)
- **Triage:** Sentinel BLOCKER = HALT (same as Roz BLOCKER). Sentinel MUST-FIX enters the triage consensus matrix alongside Poirot's findings.
- **Brain capture:** Eva captures Sentinel's findings post-review (same as Poirot -- Sentinel does not touch brain directly).

### Opt-In Flow

After Step 6 of `/pipeline-setup` (summary printed, before brain setup offer), Eva asks:

> Would you also like to enable **Sentinel** -- the security audit agent?
> It uses Semgrep (open-source SAST) to scan your code for vulnerabilities
> during QA. Requires Python and pip. Optional -- the pipeline works fine
> without it.

If yes: validate `pip`, install `semgrep-mcp`, copy persona file, register MCP server, set config flag. If no: skip entirely.

## Alternatives Considered

### A1: Poirot Enhancement (add security scanning to Poirot)

Give Poirot access to Semgrep MCP tools and add security scanning to his workflow.

**Pros:** No new agent. Simpler pipeline. One fewer parallel subagent invocation.
**Cons:** Violates Poirot's core design principle (information asymmetry -- raw diff only, no tools beyond Read/Glob/Grep/Bash). Poirot's value is specifically that he evaluates code with no context and no specialized tools. Adding Semgrep MCP tools would change his nature. Additionally, Poirot is always-on; Sentinel is opt-in. Making security scanning non-optional would force a Python dependency on all users.

**Rejected:** Poirot's information asymmetry constraint is a deliberate architectural choice documented in his persona and in multiple mandatory gates. Modifying it for security scanning undermines the blind review concept.

### A2: Security Scanning as Eva Behavior (no dedicated agent)

Eva runs Semgrep MCP tools herself before invoking Poirot, then passes findings to Poirot or Roz for interpretation.

**Pros:** No new agent. Eva already orchestrates everything.
**Cons:** Eva does not interpret findings -- she orchestrates. Adding analysis responsibilities to Eva violates the "Eva never writes code / Eva is an orchestrator" principle. Eva calling Semgrep tools then writing security findings is effectively Eva doing an agent's job. Also, Eva's context is already the most constrained in the pipeline (she carries state, not analysis).

**Rejected:** Eva orchestrates, agents analyze. Security analysis belongs in an agent.

### A3: Non-MCP Semgrep Integration (Bash-based)

Sentinel runs `semgrep` as a Bash command instead of using the MCP server. No MCP registration needed.

**Pros:** Simpler setup -- just `pip install semgrep`. No MCP server to manage.
**Cons:** Loses the structured MCP tool interface. Sentinel would need to parse CLI output manually. The MCP server provides structured findings via `semgrep_findings` tool, which is more reliable than parsing text output. Also, Semgrep team has invested in the MCP server as the primary AI integration path.

**Rejected:** MCP integration is the native path. Using Bash would be reinventing a worse version of what the MCP server provides.

## Consequences

### Positive

- Projects get automated SAST without leaving the pipeline workflow
- Sentinel findings enter the triage consensus matrix with the same rigor as Roz and Poirot findings
- Opt-in design means zero impact on projects that do not want security scanning
- Semgrep MCP is open source (LGPL 2.1) with an active maintenance team
- Information asymmetry (diff + scan results, no spec) prevents anchoring to spec intent

### Negative

- Adds a Python/pip dependency for projects that enable Sentinel (even if the project itself is not Python)
- Semgrep MCP is a third-party dependency outside the pipeline's control; breaking changes could disrupt Sentinel
- Another parallel subagent at review juncture increases token consumption and latency
- LGPL 2.1 license for Semgrep MCP -- users must understand the license implications for their project

### Neutral

- No database changes -- brain captures use existing `agent_capture` infrastructure
- `enforce-paths.sh` catch-all already blocks `sentinel` agent type from writing -- no hook changes needed
- Existing 9 core agents and their behavior are completely unchanged when Sentinel is disabled

## Implementation Plan

### Step 0: Sentinel Agent Persona File

Create `source/shared/agents/sentinel.md` with the standard persona file structure per `xml-prompt-schema.md`.

**Files to create:**
- `source/shared/agents/sentinel.md`

**Acceptance criteria:**
- YAML frontmatter: `name: sentinel`, `description: Security audit agent backed by Semgrep MCP static analysis. Runs at review juncture to identify vulnerabilities, injection risks, and security misconfigurations in changed code. Opt-in via pipeline-config.json.`, `disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit`
- `<identity>`: Sentinel, Security Audit Agent. Pronouns: they/them. Backed by Semgrep MCP. Runs on Opus model.
- `<required-actions>`: Reference to `agent-preamble.md` steps 1-5. Agent-specific: (1) Run `semgrep_scan` on changed files from diff; (2) Call `semgrep_findings` to retrieve structured results; (3) Cross-reference findings against the diff to filter noise from unchanged code; (4) Classify severity.
- `<workflow>`: Scan phase (Semgrep tools), interpret phase (diff context), report phase (structured table). Includes handling for Semgrep MCP unavailability (report as "Sentinel: scan unavailable -- Semgrep MCP not responding. Manual security review recommended.").
- `<constraints>`: Information asymmetry (no spec, no ADR, no UX doc, no context-brief). Read-only. Do not modify code. Minimum 3 findings per scan (or explicit "clean scan" with evidence). If Semgrep scan hangs or times out, STOP -- report partial results, do not retry.
- `<output>`: Structured security report with DoR/DoD, findings table (location, severity, category, CWE/OWASP reference, description, remediation), scan metadata (rules matched, files scanned, scan duration).

**Estimated complexity:** Medium (new file, must follow established persona patterns precisely)

### Step 1: Pipeline Config Template Update

Add `sentinel_enabled` field to the `pipeline-config.json` template.

**Files to modify:**
- `source/pipeline/pipeline-config.json`

**Acceptance criteria:**
- New field `"sentinel_enabled": false` added to the JSON template
- Default is `false` (opt-in, not opt-out)
- Field is at the end of the JSON object, before the closing brace

**Estimated complexity:** Low (add one JSON field)

### Step 2: Agent System Tables Update

Add Sentinel to the subagent tables in `agent-system.md` and update the phase sizing table and pipeline flow to include Sentinel conditionally.

**Files to modify:**
- `source/rules/agent-system.md` -- add Sentinel row to `<section id="architecture">` "Subagents" table
- `source/rules/agent-system.md` -- add Sentinel row to `<gate id="no-skill-tool">` agent-to-file table
- `source/rules/agent-system.md` -- update review juncture line in Phase Transitions table to include Sentinel conditionally

**Acceptance criteria:**
- Subagent table row: `| **Sentinel** | Security audit -- Semgrep-backed SAST (opt-in) | Read, Glob, Grep, Bash (read-only) + Semgrep MCP tools |`
- Agent-to-file table row: `| Sentinel (security audit) | .claude/agents/sentinel.md |`
- Phase Transitions review juncture updated: `Roz final sweep + Poirot + Robert-subagent + Sable-subagent + Sentinel (if enabled) (parallel)`
- All existing rows in both tables are unchanged
- Sentinel is clearly marked as conditional/opt-in in every mention

**Estimated complexity:** Low (add rows/notes to existing tables)

### Step 3: Triage Consensus Matrix Update

Add Sentinel column to the triage consensus matrix in `pipeline-operations.md` and add Sentinel-specific rows.

**Files to modify:**
- `source/references/pipeline-operations.md` -- update triage consensus matrix

**Acceptance criteria:**
- Matrix header row gains `Sentinel` column: `| Roz | Poirot | Robert | Sable | Sentinel | Action |`
- New row: `| any | any | any | any | BLOCKER | **HALT.** Sentinel BLOCKER (exploitable vulnerability) is always authoritative. Eva verifies Semgrep finding is not false positive (check CWE, check if code path is reachable). If confirmed, same as Roz BLOCKER. |`
- New row: `| PASS | PASS | -- | -- | MUST-FIX | **SECURITY CONCERN.** Queue fix, Colby priority. Sentinel caught what Roz and Poirot missed (SAST-specific finding). |`
- New row: `| MUST-FIX | flags issue | -- | -- | MUST-FIX | **CONVERGENT SECURITY.** Multiple reviewers flag security. High-confidence fix needed. |`
- Existing matrix rows gain a `--` in the Sentinel column (Sentinel presence does not change their behavior)
- When `sentinel_enabled: false`, the Sentinel column is absent from triage (Eva skips Sentinel entirely)

**Estimated complexity:** Medium (matrix expansion requires careful alignment of existing rows)

### Step 4: Pipeline Orchestration Update

Update `pipeline-orchestration.md` to include Sentinel in the review juncture and per-unit QA flow.

**Files to modify:**
- `source/rules/pipeline-orchestration.md` -- update review juncture section
- `source/rules/pipeline-orchestration.md` -- update pipeline flow diagram
- `source/rules/pipeline-orchestration.md` -- update mandatory gate 5 (Poirot) to note Sentinel runs in same parallel slot

**Acceptance criteria:**
- Review juncture description: "Eva invokes up to five reviewers in parallel: Roz (final sweep), Poirot (blind diff), Robert-subagent (spec, Medium/Large), Sable-subagent (UX, Large only), Sentinel (security, if `sentinel_enabled: true`)"
- Pipeline flow diagram updated to include `+ Sentinel (if enabled)` at review juncture
- Gate 5 note: "When `sentinel_enabled: true`, Sentinel also runs in parallel with Roz and Poirot after each Colby build unit, scanning changed files with Semgrep MCP."
- All changes are conditional on `sentinel_enabled` -- no behavioral change when disabled
- Sentinel failure handling: "If Sentinel invocation fails (MCP server down, scan error), Eva logs 'Sentinel audit skipped: [reason]' and proceeds. Sentinel failure is never a pipeline blocker."

**Estimated complexity:** Medium (multiple sections to update, must preserve conditional behavior)

### Step 5: Invocation Template for Sentinel

Add a `sentinel-audit` invocation template to `invocation-templates.md`.

**Files to modify:**
- `source/references/invocation-templates.md` -- add `<template id="sentinel-audit">` section

**Acceptance criteria:**
- Template follows the same XML structure as existing templates (`<task>`, `<constraints>`, `<output>`)
- No `<brain-context>` tag (Sentinel does not receive brain context -- information asymmetry)
- No `<read>` tag with spec/ADR/UX files (information asymmetry)
- `<task>`: "Security audit of Colby's build output for ADR-NNNN Step N" (per-unit) or "Security audit -- full review juncture for ADR-NNNN" (final)
- `<constraints>`: You receive ONLY the diff and Semgrep scan results. No spec, no ADR, no context. Run `semgrep_scan` on changed files. Call `semgrep_findings` for structured results. Cross-reference against the diff. Minimum 3 findings or explicit clean scan. If scan hangs, STOP.
- `<output>`: Security report with findings table, scan metadata, DoR/DoD sections

**Estimated complexity:** Low (follows established template pattern)

### Step 6: Pipeline-Setup Opt-In Flow

Update `skills/pipeline-setup/SKILL.md` to add the Sentinel opt-in step after Step 6 summary and before the brain setup offer.

**Files to modify:**
- `skills/pipeline-setup/SKILL.md` -- add Step 6a: Sentinel opt-in

**Acceptance criteria:**
- Step 6a is positioned after Step 6 summary and before "Brain setup offer"
- Eva asks: "Would you also like to enable Sentinel -- the security audit agent? It uses Semgrep (open-source SAST) to scan your code for vulnerabilities during QA. Requires Python and pip. Optional -- the pipeline works fine without it."
- If user says yes:
  1. Check `command -v pip3 || command -v pip` -- if missing, tell user to install Python/pip and skip
  2. Run `pip install semgrep-mcp` (or `pip3 install semgrep-mcp`)
  3. Copy `source/shared/agents/sentinel.md` to `.claude/agents/sentinel.md` (with placeholder customization)
  4. Register Semgrep MCP in project `.mcp.json` -- add `"semgrep": {"command": "semgrep-mcp"}` entry (flat format per MEMORY.md)
  5. Set `sentinel_enabled: true` in `.claude/pipeline-config.json`
  6. Add Sentinel to the installation summary count
- If user says no: skip entirely, `sentinel_enabled` remains `false`
- Setup summary updated to show Sentinel status: "Sentinel security agent: enabled (Semgrep MCP)" or "Sentinel security agent: not enabled"
- Installation manifest table updated with conditional Sentinel row

**Estimated complexity:** Medium (multi-step conditional flow with dependency checking)

### Step 7: Model Table Update

Add Sentinel to the fixed-model agents table in `pipeline-models.md`.

**Files to modify:**
- `source/rules/pipeline-models.md` -- add Sentinel row to fixed-model table

**Acceptance criteria:**
- New row: `| **Sentinel** | Opus | Security judgment requires strong reasoning. Semgrep provides data; Sentinel must interpret relevance, reachability, and severity in context of the diff. |`
- Sentinel is a fixed-model agent (always Opus regardless of pipeline sizing) -- same rationale as Poirot
- Existing rows unchanged

**Estimated complexity:** Low (add one table row)

### Step 8: Pipeline Operations Review Juncture Update

Update the continuous QA section in `pipeline-operations.md` to include Sentinel in the per-unit and post-build review flows.

**Files to modify:**
- `source/references/pipeline-operations.md` -- update continuous QA section (items 3, 4, 8)

**Acceptance criteria:**
- Item 3 updated: "Eva invokes Roz for QA review AND Poirot for blind diff review AND Sentinel for security audit (if `sentinel_enabled: true`) in PARALLEL"
- Item 4 updated: "Eva triages findings from all reviewers: deduplicates, classifies severity. Findings unique to Sentinel get CWE/OWASP cross-reference."
- Item 8 updated: review juncture list includes "Sentinel (security, if enabled)"
- Brain capture note: Eva captures Sentinel findings post-review via `agent_capture` with `source_agent: 'eva'`, `thought_type: 'insight'` (same pattern as Poirot -- Sentinel does not touch brain directly)

**Estimated complexity:** Low (update existing numbered items)

## Comprehensive Test Specification

### Step 0 Tests: Sentinel Persona File

| ID | Category | Description |
|----|----------|-------------|
| T-0009-001 | Happy | `source/shared/agents/sentinel.md` exists with valid YAML frontmatter containing `name: sentinel`, `description` (one-line, mentions Semgrep MCP and security), and `disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit` |
| T-0009-002 | Happy | Persona file contains `<identity>` tag with agent name "Sentinel", role "Security Audit Agent", pronouns, Semgrep MCP backing, and Opus model statement |
| T-0009-003 | Happy | `<required-actions>` references `.claude/references/agent-preamble.md` and includes Semgrep-specific steps (scan, retrieve findings, cross-reference diff, classify severity) |
| T-0009-004 | Happy | `<workflow>` defines three phases: scan (Semgrep tools), interpret (diff context), report (structured table) |
| T-0009-005 | Failure | `<workflow>` includes explicit handling for Semgrep MCP unavailability: report "scan unavailable" instead of crashing |
| T-0009-006 | Failure | `<constraints>` specifies information asymmetry: no spec, no ADR, no UX doc, no context-brief access |
| T-0009-007 | Failure | `<constraints>` specifies: if scan hangs or times out, STOP and report partial results, do not retry (retro lesson #004) |
| T-0009-008 | Happy | `<output>` specifies structured security report with findings table containing location, severity, category, CWE/OWASP reference, description, and remediation |
| T-0009-009 | Boundary | Persona file severity classification matches pipeline conventions: BLOCKER, MUST-FIX, NIT |
| T-0009-010 | Regression | All 9 existing persona files in `source/shared/agents/` are unchanged |
| T-0009-011 | Happy | XML tags follow the 7-tag order defined in `xml-prompt-schema.md`: identity, required-actions, workflow, examples, tools, constraints, output (tags without content may be omitted) |

### Step 1 Tests: Pipeline Config Template

| ID | Category | Description |
|----|----------|-------------|
| T-0009-020 | Happy | `source/pipeline/pipeline-config.json` contains `"sentinel_enabled": false` field |
| T-0009-021 | Boundary | JSON is valid and parseable by `jq` after the addition |
| T-0009-022 | Regression | All existing fields in `pipeline-config.json` are unchanged: `branching_strategy`, `platform`, `platform_cli`, `mr_command`, `merge_command`, `environment_branches`, `base_branch`, `integration_branch` |

### Step 2 Tests: Agent System Tables

| ID | Category | Description |
|----|----------|-------------|
| T-0009-030 | Happy | `source/rules/agent-system.md` `<section id="architecture">` subagent table contains a Sentinel row with role "Security audit -- Semgrep-backed SAST (opt-in)" and read-only tools + Semgrep MCP tools |
| T-0009-031 | Happy | `source/rules/agent-system.md` `<gate id="no-skill-tool">` table contains a Sentinel row mapping to `.claude/agents/sentinel.md` |
| T-0009-032 | Happy | Phase Transitions table's review juncture entry includes "Sentinel (if enabled)" |
| T-0009-033 | Regression | All existing rows in both tables are unchanged |
| T-0009-034 | Happy | Sentinel is clearly marked as conditional/opt-in in every mention |

### Step 3 Tests: Triage Consensus Matrix

| ID | Category | Description |
|----|----------|-------------|
| T-0009-040 | Happy | Matrix header row in `pipeline-operations.md` includes `Sentinel` column |
| T-0009-041 | Happy | Sentinel BLOCKER row exists: any + any + any + any + BLOCKER = HALT with verification step |
| T-0009-042 | Happy | Sentinel MUST-FIX with all others PASS row exists: treated as security concern, queue fix |
| T-0009-043 | Happy | Convergent security row exists: Sentinel MUST-FIX + Poirot flags issue = high-confidence fix |
| T-0009-044 | Boundary | Existing matrix rows gain `--` in Sentinel column (no behavioral change) |
| T-0009-045 | Failure | When `sentinel_enabled: false`, matrix description states Sentinel column is absent |
| T-0009-046 | Regression | Existing matrix rows and actions are unchanged except for the new Sentinel column |

### Step 4 Tests: Pipeline Orchestration Update

| ID | Category | Description |
|----|----------|-------------|
| T-0009-050 | Happy | Review juncture description in `pipeline-orchestration.md` lists Sentinel as the fifth parallel reviewer with conditional `(if sentinel_enabled: true)` |
| T-0009-051 | Happy | Pipeline flow diagram includes `+ Sentinel (if enabled)` at review juncture |
| T-0009-052 | Happy | Gate 5 (Poirot) includes note about Sentinel running in same parallel slot when enabled |
| T-0009-053 | Failure | Sentinel failure handling documented: MCP server down = log warning and proceed, never block pipeline |
| T-0009-054 | Regression | All mandatory gates (1-12) retain their existing behavior; no gate is removed or weakened |
| T-0009-055 | Boundary | All Sentinel mentions are conditional on `sentinel_enabled` -- disabled pipeline behavior is unchanged |

### Step 5 Tests: Invocation Template

| ID | Category | Description |
|----|----------|-------------|
| T-0009-060 | Happy | `source/references/invocation-templates.md` contains `<template id="sentinel-audit">` section |
| T-0009-061 | Happy | Template has `<task>` tag describing security audit scope |
| T-0009-062 | Happy | Template has `<constraints>` specifying: diff only, Semgrep scan results, no spec/ADR/UX, minimum 3 findings or clean scan, stop if scan hangs |
| T-0009-063 | Happy | Template has `<output>` specifying security report format with DoR/DoD |
| T-0009-064 | Failure | Template does NOT include `<brain-context>` tag (information asymmetry) |
| T-0009-065 | Failure | Template does NOT include `<read>` with spec, ADR, or UX files (information asymmetry) |
| T-0009-066 | Regression | All existing templates in `invocation-templates.md` are unchanged |

### Step 6 Tests: Pipeline-Setup Opt-In

| ID | Category | Description |
|----|----------|-------------|
| T-0009-070 | Happy | SKILL.md contains Step 6a positioned after Step 6 summary and before brain setup offer |
| T-0009-071 | Happy | Step 6a asks user about Sentinel with explanation of what it does and what it requires (Python, pip) |
| T-0009-072 | Happy | "Yes" path: checks pip availability, installs semgrep-mcp, copies persona, registers MCP, sets config flag |
| T-0009-073 | Happy | MCP registration uses flat format: `"semgrep": {"command": "semgrep-mcp"}` in project `.mcp.json` |
| T-0009-074 | Failure | "No" path: skips entirely, `sentinel_enabled` remains `false`, no files modified |
| T-0009-075 | Failure | Missing pip: tells user to install Python/pip and skips Sentinel setup (does not error) |
| T-0009-076 | Happy | Setup summary includes Sentinel status line |
| T-0009-077 | Happy | Installation manifest table includes conditional Sentinel row |
| T-0009-078 | Regression | Existing SKILL.md steps 1-6 are unchanged |
| T-0009-079 | Boundary | Step 6a handles existing `.mcp.json` (merges, does not overwrite) vs. no existing `.mcp.json` (creates) |
| T-0009-080 | Security | Sentinel persona copied to `.claude/agents/`, not left in plugin's native directory |

### Step 7 Tests: Model Table

| ID | Category | Description |
|----|----------|-------------|
| T-0009-090 | Happy | `source/rules/pipeline-models.md` fixed-model table contains Sentinel row with Opus model |
| T-0009-091 | Happy | Rationale references security judgment and Semgrep data interpretation |
| T-0009-092 | Regression | All existing model table rows are unchanged |

### Step 8 Tests: Pipeline Operations Update

| ID | Category | Description |
|----|----------|-------------|
| T-0009-100 | Happy | Continuous QA item 3 includes Sentinel in parallel with Roz and Poirot (conditional) |
| T-0009-101 | Happy | Continuous QA item 4 includes Sentinel in triage (with CWE/OWASP cross-reference note) |
| T-0009-102 | Happy | Continuous QA item 8 (review juncture) includes Sentinel |
| T-0009-103 | Happy | Brain capture note for Sentinel follows Poirot pattern: Eva captures via `agent_capture` with `source_agent: 'eva'`, `thought_type: 'insight'` |
| T-0009-104 | Regression | All existing continuous QA items retain their behavior |
| T-0009-105 | Boundary | All Sentinel mentions conditional on `sentinel_enabled: true` |

### Step 0-8 Telemetry

| Step | Telemetry | Trigger | Absence Means |
|------|-----------|---------|---------------|
| Step 0 | Sentinel persona file exists and is parseable | `/pipeline-setup` with Sentinel enabled | Persona file missing or malformed |
| Step 1 | `pipeline-config.json` contains `sentinel_enabled` field | Every pipeline boot (Eva reads config) | Config template not updated |
| Step 4 | Eva announcement: "Invoking Sentinel for security audit" or "Sentinel audit skipped: [reason]" | Review juncture when `sentinel_enabled: true` | Sentinel invocation silently skipped or failed without logging |
| Step 5 | Eva delegation contract includes Sentinel's READ and CONSTRAINTS | Every Sentinel invocation | Silent invocation -- transparency violation |
| Step 6 | Setup summary: "Sentinel security agent: enabled/not enabled" | Every `/pipeline-setup` run | Opt-in step silently skipped |
| Step 8 | Brain capture: "Sentinel security audit: [N findings]. Categories: [list]." | After Sentinel returns at review juncture (brain available) | Eva did not capture Sentinel findings |

### Contract Boundaries

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| Semgrep MCP (`semgrep_scan`) | Structured scan results (rules matched, findings with locations) | Sentinel agent (interprets and classifies) | Step 0 (persona defines how to call and interpret) |
| Sentinel agent output | Security report: `{findings_table, scan_metadata, severity_counts}` | Eva (triage consensus matrix) | Step 3, Step 4 |
| Eva diff extraction (`git diff`) | Raw diff text | Sentinel agent (scope filter for findings) | Step 5 (invocation template) |
| `pipeline-config.json` (`sentinel_enabled`) | Boolean flag | Eva (gates all Sentinel behavior) | Step 1, Step 4, Step 6 |
| `/pipeline-setup` opt-in | Installs persona + MCP + config | Runtime pipeline | Step 6 -> all other steps |

## Anti-Goals

1. **Anti-goal: Custom Semgrep rule authoring or management within the pipeline.** Reason: Sentinel uses Semgrep's default rulesets and any rules the user has configured independently. The pipeline does not manage Semgrep rule configuration, custom rule creation, or rule suppression. Revisit: if users need project-specific security rules that should be version-controlled and pipeline-managed.

2. **Anti-goal: Replacing or reducing Poirot's security checks.** Reason: Poirot's manual security review (logic-level, not SAST) and Sentinel's automated SAST are complementary. Poirot catches semantic security issues (auth logic flaws, business logic bypasses) that SAST tools miss. Sentinel catches pattern-based vulnerabilities (injection, XSS, deserialization) that LLM review may miss. Both run. Revisit: never -- this is a design principle.

3. **Anti-goal: Making Sentinel mandatory or adding it to mandatory gates.** Reason: Sentinel is opt-in because it adds a Python/pip dependency. The pipeline must work identically without it. Adding a mandatory gate for Sentinel would break the "zero impact when disabled" principle. Revisit: if Semgrep MCP becomes available without Python (e.g., as a standalone binary or Node.js package).

## Blast Radius

### Files Created (all in `source/`)

| File | Impact |
|------|--------|
| `source/shared/agents/sentinel.md` | New agent persona file -- installed to `.claude/agents/sentinel.md` by setup |

### Files Modified

| File | Change Type | Impact |
|------|-------------|--------|
| `source/pipeline/pipeline-config.json` | Add `sentinel_enabled` field | Config template for all target projects |
| `source/rules/agent-system.md` | Add Sentinel rows to subagent table, no-skill-tool table, phase transitions | Agent architecture documentation for all target projects |
| `source/references/pipeline-operations.md` | Add Sentinel column to triage matrix, update continuous QA items | Operational procedures for all target projects |
| `source/rules/pipeline-orchestration.md` | Update review juncture, pipeline flow, gate 5 note | Pipeline flow documentation for all target projects |
| `source/references/invocation-templates.md` | Add sentinel-audit template | Eva's invocation reference |
| `skills/pipeline-setup/SKILL.md` | Add Step 6a opt-in flow | Setup user experience |
| `source/rules/pipeline-models.md` | Add Sentinel row to fixed-model table | Model selection reference |

### Files NOT Modified (verified no changes needed)

| File | Reason |
|------|--------|
| `source/claude/hooks/enforce-paths.sh` | Catch-all `*)` at line 112 already blocks `sentinel` agent type from writing -- correct default behavior |
| `source/claude/hooks/enforce-sequencing.sh` | No sequencing gates needed for Sentinel -- it runs in parallel at review juncture, not in a sequencing-sensitive position |
| `source/claude/hooks/enforcement-config.json` | No new config keys needed -- Sentinel is read-only, gated by `pipeline-config.json` |
| `source/shared/agents/*.md` (all 9 existing) | Existing agents unchanged |
| `source/commands/*.md` (all 7) | No new slash command for Sentinel -- invoked by Eva at review juncture |
| `source/rules/default-persona.md` | Eva's boot sequence does not need changes; `sentinel_enabled` is read from `pipeline-config.json` (already read at step 3b) |
| `source/references/agent-preamble.md` | Sentinel references it, preamble does not reference Sentinel |
| `source/references/xml-prompt-schema.md` | No new tags -- Sentinel uses existing persona tag vocabulary |
| `.mcp.json` (plugin-level) | Semgrep MCP is registered in the target project's `.mcp.json`, not the plugin's |

### Consumers of Modified Files

| File | Consumers |
|------|-----------|
| `source/shared/agents/sentinel.md` | `skills/pipeline-setup/SKILL.md` (copies to `.claude/agents/`), Claude Code subagent system |
| `source/pipeline/pipeline-config.json` | `skills/pipeline-setup/SKILL.md` (copies to `.claude/`), Eva boot sequence |
| `source/rules/agent-system.md` | `skills/pipeline-setup/SKILL.md` (copies to `.claude/rules/`), all target projects |
| `source/references/pipeline-operations.md` | `skills/pipeline-setup/SKILL.md` (copies to `.claude/references/`), Eva at pipeline start |
| `source/rules/pipeline-orchestration.md` | `skills/pipeline-setup/SKILL.md` (copies to `.claude/rules/`), Eva when reading `docs/pipeline/` files |
| `source/references/invocation-templates.md` | `skills/pipeline-setup/SKILL.md` (copies to `.claude/references/`), Eva when constructing invocations |
| `source/rules/pipeline-models.md` | `skills/pipeline-setup/SKILL.md` (copies to `.claude/rules/`), Eva for model selection |
| `skills/pipeline-setup/SKILL.md` | Plugin skill system (invoked via `/pipeline-setup`) |

## Data Sensitivity

Not applicable -- Sentinel does not introduce data access methods, stores, or persistent state. All findings are ephemeral (exist only in the subagent's output and Eva's triage).

## Notes for Colby

1. **Step ordering matters.** Step 0 (persona file) should be first because other steps reference it. Step 1 (config) should be second because Steps 2-8 reference `sentinel_enabled`. Steps 2-5, 7-8 can be done in any order after 0 and 1. Step 6 (SKILL.md) should be last because it references the persona file path and config field.

2. **Persona file pattern.** Model the persona file closely on `source/shared/agents/investigator.md` (Poirot). Both are read-only reviewers with information asymmetry. Key differences: Sentinel has Semgrep MCP tools available, Sentinel's workflow centers on SAST results rather than pure diff analysis, Sentinel includes CWE/OWASP references in findings.

3. **Triage matrix expansion.** When adding the Sentinel column, ensure existing rows get `--` (dash-dash) in the new column, meaning "Sentinel's verdict does not change this row's action." Only add new rows for Sentinel-specific scenarios. Do not duplicate existing rows.

4. **MCP registration format.** Per MEMORY.md (`feedback_plugin_mcp_format.md`), the `.mcp.json` uses flat format, not wrapped. The Semgrep MCP entry should be: `"semgrep": {"command": "semgrep-mcp"}`. The setup flow must handle both "`.mcp.json` exists" (merge) and "`.mcp.json` does not exist" (create) cases.

5. **Conditional language pattern.** Every mention of Sentinel in modified files must be conditional: "if `sentinel_enabled: true`" or "(if enabled)" or "(opt-in)". This makes it unambiguous that Sentinel is gated. Follow the same pattern used for Sable at review juncture: "Sable-subagent (UX, Large only)" becomes "Sentinel (security, if enabled)".

6. **`enforce-paths.sh` catch-all is the safety net.** The catch-all `*)` case at line 112-118 blocks ALL unknown agent types from Write/Edit/MultiEdit. `sentinel` will match this catch-all because it is not `cal`, `colby`, `roz`, `ellis`, `agatha`, or `""` (main thread). This is correct -- do NOT add a `sentinel)` case to the hook. Sentinel is read-only.

7. **Brain capture for Sentinel findings.** Follows the exact same pattern as Poirot: Eva captures Sentinel findings post-review via `agent_capture` with `source_agent: 'eva'`, `thought_type: 'insight'`. Sentinel itself never touches brain. This is documented in `pipeline-orchestration.md` brain capture protocol.

8. **Semgrep MCP tool names.** The Semgrep MCP server exposes: `security_check`, `semgrep_scan`, `semgrep_scan_with_custom_rule`, `get_abstract_syntax_tree`, `semgrep_findings`. Sentinel's core workflow uses `semgrep_scan` (run scan) and `semgrep_findings` (retrieve results). `security_check` is a convenience wrapper. Do not reference tools that may not exist -- stick to the documented set from the Semgrep MCP README.

9. **SKILL.md placement.** The opt-in question goes after the Step 6 summary (file count, tree, commands) and before "Brain setup offer (always ask):" block. This means the user sees their pipeline is fully installed, then gets asked about the optional security agent, then gets asked about brain. The ordering is: required setup -> optional security -> optional memory.

## DoD: Verification

| Requirement | Step | Test IDs | Status |
|-------------|------|----------|--------|
| R1: Sentinel is optional, user opts in during setup | Step 1, Step 6 | T-0009-020, T-0009-070 through T-0009-080 | Designed |
| R2: Full install chain (pip, persona, MCP, config) | Step 6 | T-0009-072, T-0009-073, T-0009-080 | Designed |
| R3: Semgrep MCP backbone with specific tools | Step 0, Step 5 | T-0009-003, T-0009-004, T-0009-062 | Designed |
| R4: Runs at review juncture parallel with others | Step 4, Step 8 | T-0009-050, T-0009-100 through T-0009-102 | Designed |
| R5: Read-only access | Step 0 | T-0009-001, T-0009-006 | Designed |
| R6: Security BLOCKER = pipeline halt | Step 3 | T-0009-041 | Designed |
| R7: `pipeline-config.json` gets `sentinel_enabled` | Step 1 | T-0009-020 through T-0009-022 | Designed |
| R8: Information asymmetry (diff + scan, no spec/ADR) | Step 0, Step 5 | T-0009-006, T-0009-064, T-0009-065 | Designed |
| R9: All changes in `source/` and `skills/` only | All | Blast radius table | Designed |
| R10: XML format per schema | Step 0 | T-0009-011 | Designed |
| R11: Triage matrix updated | Step 3 | T-0009-040 through T-0009-046 | Designed |
| R12: Invocation template added | Step 5 | T-0009-060 through T-0009-066 | Designed |
| R13: Agent system tables updated | Step 2 | T-0009-030 through T-0009-034 | Designed |
| R14: Setup flow after Step 6, before brain | Step 6 | T-0009-070, T-0009-078 | Designed |
| R15: Persona in `source/shared/agents/`, installed to `.claude/agents/` | Step 0, Step 6 | T-0009-001, T-0009-080 | Designed |
| R16: Mechanical enforcement via hook catch-all | Blast radius (no changes) | T-0009-001 (disallowedTools), Notes for Colby #6 | Designed (existing behavior preserved) |

### Architectural Decisions Not in Spec

1. **Sentinel runs at per-unit QA AND review juncture:** The context-brief specifies "runs at review juncture." The ADR extends this to also run per-unit (parallel with Roz and Poirot) because security issues should be caught early, not deferred to the end. This is consistent with how Poirot already works (per-unit + review juncture).
2. **Sentinel failure is never a pipeline blocker:** Unlike Roz (whose absence blocks the pipeline), Sentinel failure (MCP down, scan error) produces a warning and the pipeline proceeds. This maintains the "pipeline works fine without it" principle even when Sentinel is enabled but broken.
3. **Fixed Opus model:** Sentinel is always Opus regardless of pipeline sizing. Security analysis requires strong reasoning to evaluate whether a Semgrep finding is a real vulnerability in context. This matches the rationale for Poirot (blind review with minimal context needs strong reasoning).
4. **No slash command for Sentinel:** Sentinel is invoked by Eva at review juncture, not manually by the user. There is no `/security` command. Users who want ad-hoc security scanning can ask Eva directly and she will route to Sentinel if enabled.

### Rejected During Design

1. **Adding Sentinel to mandatory gates:** Would make Sentinel non-optional by definition. A mandatory gate cannot be skipped, but Sentinel must be skippable when disabled.
2. **Sentinel as a skill (main thread):** Would consume Eva's context window with Semgrep output. Subagent gets its own context window, which is better for processing scan results.
3. **Registering Semgrep MCP at plugin level (`.mcp.json` in plugin root):** Would make Semgrep MCP load for ALL projects using the plugin, even those without Sentinel enabled. Must be project-level registration.

### Technical Constraints Discovered

1. `enforce-paths.sh` line 112-118: Catch-all blocks `sentinel` agent type from writing. Correct behavior, no changes needed.
2. `.mcp.json` uses flat format (per MEMORY.md `feedback_plugin_mcp_format.md`). Semgrep MCP registration must follow this format.
3. `pipeline-config.json` is read by Eva at boot (step 3b reads branching strategy from this file). Adding `sentinel_enabled` to the same file means Eva reads it naturally -- no new file read needed.

---

ADR saved to `docs/architecture/ADR-0009-sentinel-security-agent.md`. 9 steps (0-8), 55 total tests. Next: Roz reviews the test spec.
