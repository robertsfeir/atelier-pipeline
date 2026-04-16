# ADR-0040: Design System Auto-Loading

## Status

Proposed

## DoR: Requirements Extracted

**Sources:** Conversational design decisions (context-brief), `source/shared/agents/sable-ux.md`, `source/shared/agents/sable.md`, `source/shared/agents/colby.md`, `source/shared/agents/cal.md`, `source/shared/pipeline/pipeline-config.json`

| # | Requirement | Source | Citation |
|---|-------------|--------|----------|
| 1 | Auto-detect `design-system/` at project root -- no config required | Conversation | Convention-over-configuration decision |
| 2 | Design files live in the PROJECT root (committed to git), NOT in `.claude/` | Conversation | Separation of concerns decision |
| 3 | Reference in place, do not copy -- `pipeline-config.json` stores path override only | Conversation | External path case |
| 4 | Selective loading: `tokens.md` always + 1 domain file based on work type | Conversation | Loading table |
| 5 | `/load-design` skill sets `design_system_path` override in `pipeline-config.json` | Conversation | External path case only |
| 6 | SVG icons stay as SVG -- no conversion | Conversation | Explicit constraint |
| 7 | Graceful absence: no `design-system/` AND no override = behavior unchanged, no errors | Conversation | Constraint |
| 8 | Sable notes which design system files she loaded (or "no design system found") | Conversation | Transparency requirement |
| 9 | Colby loads the same files Sable loaded -- consistency, not re-detection | Conversation | Cross-agent consistency |
| 10 | Loading logic described in prose in agent personas (not a separate script) | Conversation | Implementation constraint |
| 11 | Colby references `design-system/icons/*.svg` directly in generated HTML/CSS | Conversation | Icon handling |
| 12 | All edits in `source/` only -- pipeline-setup syncs to `.claude/` | CLAUDE.md | Source structure note |

**Retro risks:**
- Lesson 005 (Frontend Wiring Omission): Design system context crosses agent boundaries. Sable produces UX docs referencing design tokens, Colby consumes them. If Colby does not load the same design system files, tokens drift. Mitigated by requirement 9 (Colby loads what Sable loaded), propagated via `<read>` not `<constraints>` (lessons 005/006).
- Lesson 005/006 (Cross-agent context propagation): Cal designs without searching institutional memory unless Eva happens to inject brain context. If Eva misses a search term or brain is down, Cal repeats past mistakes. Mitigated by adding a mandatory brain-search DoR step to Cal's workflow.

## Context

Agents currently generate UI with no awareness of whether a project has an established design system. Sable produces UX docs that reference colors, spacing, and typography from intuition. Colby implements UI from those docs plus professional defaults. When a project has an existing design system (tokens, component patterns, navigation conventions), this disconnect produces drift between the design system and the generated output.

The Kyro design system is the reference implementation -- a set of Markdown files describing tokens (colors, spacing, typography), component patterns, navigation conventions, data visualization guidelines, layout patterns for web and app, and an icon library (SVG assets). Other projects may have different design systems with different file structures, but the convention assumes a predictable directory shape.

## Decision

**Convention-first auto-loading with optional path override.**

### Detection Order

1. Read `design_system_path` from `pipeline-config.json`. If non-null and non-empty, use that path.
2. Else, check if `design-system/` exists at the project root.
3. If neither exists, proceed without a design system. No error, no warning beyond agent-level annotation ("no design system found").

### Selective Loading Rules

When a design system is detected, agents load `tokens.md` (always) plus one domain-specific file based on the work being done:

| Building... | Load |
|---|---|
| Any UI | `tokens.md` (always) |
| Components, forms | + `components.md` |
| Navigation | + `navigation.md` |
| Dashboards, data display | + `data-viz.md` |
| Marketing/web pages | + `layouts-web.md` |
| App screens | + `layouts-app.md` |

Domain file selection is based on the ADR step description or UX doc section being worked on. If ambiguous, load `components.md` as the default domain file. If the domain file does not exist at the resolved path, log "design system file [name] not found -- proceeding without it" and continue.

### Cross-Agent Consistency

Sable-ux (producer) loads design system files during UX doc production and records which files she loaded in her output. Sable (reviewer) references the same files when verifying implementation. Colby loads the same design system files that were loaded for the feature's UX phase. Eva passes the loaded file list in Colby's invocation `<read>` tag (not `<constraints>`) to ensure consistency without re-detection. The `<read>` tag fires before the agent begins work, making the design system files available as first-class context rather than prose instructions the agent may deprioritize.

**Why `<read>` and not `<constraints>`:** Retro lessons 005 and 006 both demonstrate that behavioral constraints do not survive subagent context window boundaries. In both cases, the fix was adding the missing artifact to the downstream agent's `<read>` list. `<constraints>` is prose a subagent may ignore; `<read>` is mechanical -- it populates the agent's context window before execution begins.

### Icon Handling

Colby references SVG files from `design-system/icons/*.svg` (or the override path equivalent) directly in generated HTML/CSS. No format conversion. Icon file names are treated as the icon vocabulary -- Colby reads the directory listing to discover available icons.

### Pipeline Config Schema Addition

Add `design_system_path` to `pipeline-config.json`:

```json
{
  "design_system_path": null
}
```

- Type: `string | null`
- Default: `null` (convention-based detection)
- When set: absolute or project-relative path to the design system directory
- Set by: `/load-design` skill or manual edit

### `/load-design` Skill Specification

**Purpose:** Sets `design_system_path` in `pipeline-config.json` for projects whose design system lives outside the project root (e.g., a shared monorepo package, a sibling directory).

**Inputs:**
- `path` (required): Path to the design system directory. Absolute or relative to project root.

**Behavior:**
1. Validate the path exists and contains at least `tokens.md`. If `tokens.md` is missing, reject: "Path [X] does not contain tokens.md -- not a valid design system directory."
2. Read current `pipeline-config.json`.
3. Set `design_system_path` to the provided path (resolve to absolute if relative).
4. Write updated `pipeline-config.json`.
5. List discovered design system files at the path (all `.md` files and `icons/` directory if present).

**Output:** "Design system path set to [path]. Found: [list of files]. Agents will use this path for design system loading."

**Error cases:**
- Path does not exist: "Directory [path] not found."
- Path exists but no `tokens.md`: "No tokens.md found at [path]. A valid design system must include tokens.md."
- `pipeline-config.json` not found: "Pipeline not installed. Run /pipeline-setup first."

**Reset:** User can clear the override by running `/load-design` with path `reset` or by setting `design_system_path: null` manually. When cleared, agents fall back to convention-based detection (`design-system/` at project root).

## Anti-Goals

**Anti-goal: Automated design system generation.** Reason: This feature loads an existing design system, it does not create one. Generating tokens.md from a Figma export or CSS variables is a separate concern with different complexity. Revisit: when 3+ users request "bootstrap a design system from my existing CSS."

**Anti-goal: Design system validation or linting.** Reason: We detect and load files, we do not enforce that the design system is internally consistent or complete. A design system with only `tokens.md` is valid. Revisit: when Roz could meaningfully flag "your tokens.md defines `--color-primary` but your components.md references `--brand-primary`."

**Anti-goal: Runtime design system switching.** Reason: A pipeline run targets one design system. Switching mid-pipeline (e.g., "now use the dark theme variant") requires re-doing all UX work. The `design_system_path` override is session-scoped, not step-scoped. Revisit: when multi-theme support becomes a product requirement.

## Spec Challenge

**The spec assumes `tokens.md` is sufficient as the validity marker.** If wrong, the design fails because a directory containing only a `tokens.md` with unrelated content (e.g., crypto token documentation) would be treated as a design system, injecting garbage context into Sable and Colby. The mitigation is narrow: `tokens.md` must be inside a `design-system/` directory (convention path) or explicitly set via `/load-design` (user-intentional path). The convention path provides structural validation (directory name + file name). The override path relies on user intent (they explicitly pointed us there).

**SPOF: Eva's invocation `<read>` list assembly.** Failure mode: Eva forgets to include the design system file list in Colby's `<read>` tag, causing Colby to re-detect (possibly with different results if files changed between Sable's run and Colby's run) or to skip loading entirely. Graceful degradation: Colby's DoR includes a design system check. If no design system files are listed in `<read>` AND no `design-system/` directory exists, Colby proceeds without one (current behavior). If `design-system/` exists but `<read>` omits it, Colby loads it herself -- this is redundant but safe. The worst case is inconsistency, not failure. The `<read>` mechanism is stronger than the prior `<constraints>` approach (retro lessons 005/006) but is still not mechanically enforced -- it depends on Eva constructing the invocation correctly.

## Alternatives Considered

### 1. Design system files inside `.claude/references/`

Rejected. Design system files are project assets, not pipeline configuration. They should be version-controlled with the project, not mixed with agent personas and orchestration rules. A design system may be shared across multiple projects -- storing it in `.claude/` couples it to the pipeline installation.

### 2. Copy design system files into agent context at pipeline start

Rejected. Copying creates staleness risk -- if the design system is updated during a pipeline run, agents work from stale copies. Reference-in-place ensures agents always read the current version.

### 3. Mandatory configuration in `pipeline-config.json`

Rejected. Convention-over-configuration is the right default. Most projects will have `design-system/` at the root. Requiring explicit configuration adds friction for the common case and provides no benefit -- the detection is trivial.

### 4. Load all design system files for every agent invocation

Rejected. Design system files can be substantial. Loading `layouts-web.md` when building a dashboard component wastes context window. Selective loading keeps agent context focused.

## Consequences

**Positive:**
- Zero-config for projects that follow the convention (`design-system/` at root)
- Design-aware UI generation from both Sable (design phase) and Colby (build phase)
- Consistent design language across pipeline output
- SVG icons referenced directly -- no lossy conversion
- Graceful degradation when no design system exists

**Negative:**
- Agents read additional files per invocation (tokens.md + 1 domain file) -- modest context cost
- Cross-agent consistency depends on Eva correctly assembling Colby's `<read>` list (mechanical via `<read>`, but Eva's list assembly is behavioral)
- No mechanical enforcement that Colby actually uses the loaded tokens -- behavioral only

**Neutral:**
- `pipeline-config.json` gains one new nullable key
- One new skill file (`/load-design`)

## Implementation Plan

### Step 1: Pipeline Config Schema + Design System Reference Doc

**Files to modify:**
- `source/shared/pipeline/pipeline-config.json` (add `design_system_path` key)

**Files to create:**
- `source/shared/references/design-system-loading.md` (loading rules reference)

**Acceptance criteria:**
- `pipeline-config.json` template includes `"design_system_path": null` after existing keys
- `design-system-loading.md` contains detection order, selective loading table, cross-agent consistency rules, icon handling rules, and expected directory structure
- Reference doc is self-contained -- an agent can follow it without reading the ADR

**After this step, I can:** point agents at a reference doc that describes exactly how design system loading works.

**Complexity:** Low (2 files, schema addition + prose doc)

### Step 2: Sable-UX (Producer) Design System Integration

**Files to modify:**
- `source/shared/agents/sable-ux.md` (add design system DoR check and loading behavior)

**Acceptance criteria:**
- Sable-ux's `<workflow>` includes a step 0 or step 1a: "Check for design system" using detection order from reference doc
- Sable-ux loads `tokens.md` + domain file per the selective loading table
- Sable-ux's output includes a "Design System" annotation: either "Loaded: [file list]" or "No design system found"
- When design system is loaded, Sable-ux references its tokens (colors, spacing, typography) in her UX doc output
- The `<constraints>` section references `design-system-loading.md`

**After this step, I can:** run Sable-ux on a project with a `design-system/` directory and see her UX doc reference the design system's tokens.

**Complexity:** Low (1 file, prose additions to workflow/constraints/output)

### Step 3: Sable (Reviewer) Design System Awareness

**Files to modify:**
- `source/shared/agents/sable.md` (add design system reference in verification)

**Acceptance criteria:**
- Sable's `<workflow>` includes: "If design system files were loaded during UX production (noted in UX doc), read the same files to verify implementation uses the correct tokens"
- Sable checks implementation CSS/HTML against design system tokens when available
- Sable does NOT auto-detect design system independently -- she reads what the UX doc says was loaded
- New DRIFT category: "Design System Deviation" -- implementation uses hardcoded values instead of design system tokens

**After this step, I can:** have Sable catch when Colby hardcodes `#3B82F6` instead of using the design system's `--color-primary`.

**Complexity:** Low (1 file, prose additions to workflow/constraints)

### Step 4: Colby Design System Integration

**Files to modify:**
- `source/shared/agents/colby.md` (add design system DoR check and loading behavior)

**Acceptance criteria:**
- Colby's `<workflow>` Build Mode includes: "Check for design system files in `<read>` list or detect via convention"
- Colby loads the same design system files that Sable loaded (from Eva's `<read>` tag, or by re-detecting if `<read>` omits them)
- Colby's DoR UI Contract table gains a "Design system" row: `[tokens.md + domain file loaded, or "None"]`
- Colby references SVG icons from `design-system/icons/` directly in generated HTML/CSS
- Colby uses design system tokens (CSS custom properties, spacing values, typography) instead of hardcoded values when a design system is loaded
- The `<constraints>` section references `design-system-loading.md`

**After this step, I can:** have Colby generate UI that uses the project's design system tokens and icons.

**Complexity:** Low (1 file, prose additions to workflow/constraints/output)

### Step 5: `/load-design` Skill + Pipeline-Setup Integration

**Files to create:**
- `skills/load-design/SKILL.md` (skill file for external design system path override)

**Files to modify:**
- `skills/pipeline-setup/SKILL.md` (add `design_system_path` to pipeline-config template and installation manifest)

**Acceptance criteria:**
- `/load-design` skill validates path exists and contains `tokens.md`
- `/load-design` sets `design_system_path` in `pipeline-config.json`
- `/load-design` supports `reset` to clear the override
- `/load-design` lists discovered files at the path
- `pipeline-setup` references `design_system_path` in the pipeline-config template section
- Error messages are specific: path not found, no tokens.md, pipeline not installed

**After this step, I can:** point the pipeline at an external design system via `/load-design /path/to/shared-design-system`.

**Complexity:** Low (1 new file, 1 modification; skill is simple read-validate-write)

### Step 6: Cal Brain-Search DoR Step

**Files to modify:**
- `source/shared/agents/cal.md` (add mandatory brain-search step to workflow)

**Acceptance criteria:**
- Cal's `<workflow>` gains a new first step (before any design work): "Search institutional memory"
- When brain available (check `pipeline-state.md`): Cal calls `agent_search` for prior decisions, lessons, and ADRs touching the same domain as the feature being designed, and injects findings into DoR "Retro risks" field
- When brain unavailable: Cal reads `retro-lessons.md` AND greps `docs/architecture/` for prior ADRs on related domains
- Either path: Cal notes relevant findings in DoR before proceeding; this step is mandatory, not optional
- The step is unconditional -- it runs for every ADR, not just design system work

**After this step, I can:** have Cal actively search for prior institutional knowledge before designing, rather than relying passively on Eva's brain context injection.

**Complexity:** Low (1 file, prose addition to workflow)

## Test Specification

### Detection and Loading

| ID | Category | Description | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| T-0040-001 | Happy path | `design-system/` exists at project root with `tokens.md` | Agent loads `tokens.md` from `design-system/tokens.md` | Agent does not read `tokens.md` or reads from wrong path |
| T-0040-002 | Happy path | `design_system_path` set in `pipeline-config.json` to valid path | Agent loads from configured path, ignores `design-system/` at root | Agent loads from root convention instead of configured path |
| T-0040-003 | Failure | No `design-system/` at root AND no `design_system_path` configured | Agent proceeds normally, annotates "no design system found" | Agent errors, blocks, or silently omits annotation |
| T-0040-004 | Failure | `design_system_path` points to non-existent directory | Agent falls back to convention check, then proceeds without design system | Agent crashes or uses stale/wrong path |
| T-0040-005 | Failure | `design-system/` exists but `tokens.md` is missing | Agent logs "tokens.md not found" and proceeds without design system | Agent loads other files without tokens or crashes |
| T-0040-006 | Edge case | Both `design-system/` at root AND `design_system_path` configured | Agent uses `design_system_path` (config overrides convention) | Agent loads from convention path |

### Selective Loading

| ID | Category | Description | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| T-0040-007 | Happy path | Step description mentions "dashboard" or "data display" | Agent loads `tokens.md` + `data-viz.md` | Agent loads wrong domain file or loads all files |
| T-0040-008 | Happy path | Step description mentions "navigation" | Agent loads `tokens.md` + `navigation.md` | Agent loads wrong domain file |
| T-0040-009 | Happy path | Step description mentions "component" or "form" | Agent loads `tokens.md` + `components.md` | Agent loads wrong domain file |
| T-0040-010 | Edge case | Step description is ambiguous (no clear domain match) | Agent loads `tokens.md` + `components.md` (default) | Agent loads no domain file or loads all files |
| T-0040-011 | Failure | Domain file specified by loading table does not exist in design system | Agent logs missing file and proceeds with `tokens.md` only | Agent crashes or blocks |

### Cross-Agent Consistency

| ID | Category | Description | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| T-0040-012 | Happy path | Sable-ux loads `tokens.md` + `components.md`; Eva includes those files in Colby's `<read>` tag | Colby's context contains same files (tokens.md + components.md) before execution begins | Colby loads different files or skips design system |
| T-0040-013 | Happy path | Sable-ux annotates "Loaded: tokens.md, navigation.md" in output | Output contains design system annotation with exact file list | Annotation missing or lists wrong files |
| T-0040-014 | Edge case | Eva omits design system files from Colby's `<read>` but `design-system/` exists | Colby re-detects and loads design system (redundant but safe) | Colby proceeds without design system despite it existing |
| T-0040-014a | Failure | Eva passes design system files via `<constraints>` instead of `<read>` | Treated as a propagation defect -- Colby may not load the files (retro lessons 005/006) | Colby reliably loads files from `<constraints>` (contradicts retro evidence) |

### `/load-design` Skill

| ID | Category | Description | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| T-0040-015 | Happy path | User runs `/load-design /path/to/valid/dir` (contains `tokens.md`) | `design_system_path` set in pipeline-config.json; file list displayed | Path not set or wrong path stored |
| T-0040-016 | Failure | User runs `/load-design /nonexistent/path` | Error: "Directory /nonexistent/path not found" | Silent failure or partial config update |
| T-0040-017 | Failure | User runs `/load-design /path/without/tokens` | Error: "No tokens.md found at /path/without/tokens" | Path accepted without tokens.md |
| T-0040-018 | Happy path | User runs `/load-design reset` | `design_system_path` set to `null`; confirmation message | Key removed entirely or set to empty string |
| T-0040-019 | Failure | User runs `/load-design` without pipeline installed | Error: "Pipeline not installed. Run /pipeline-setup first." | Crashes or creates partial config |

### Sable Reviewer (Design System Deviation)

| ID | Category | Description | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| T-0040-020 | Happy path | UX doc notes "design system loaded: tokens.md"; implementation uses hardcoded `#3B82F6` instead of `--color-primary` | Sable flags DRIFT: "Design System Deviation" with file:line | Sable misses the deviation |
| T-0040-021 | Edge case | UX doc notes "no design system found" | Sable skips design system verification entirely | Sable attempts to verify against non-existent design system |

### Icon Handling

| ID | Category | Description | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| T-0040-022 | Happy path | `design-system/icons/` exists with SVG files | Colby references `.svg` files directly in generated HTML/CSS | Colby converts to WebP/PNG or ignores icons |
| T-0040-023 | Edge case | `design-system/icons/` does not exist | Colby proceeds without icon references | Colby errors or creates broken icon references |

### Pipeline Config

| ID | Category | Description | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| T-0040-024 | Happy path | Fresh `pipeline-config.json` from template | Contains `"design_system_path": null` | Key missing from template |
| T-0040-025 | Edge case | Existing `pipeline-config.json` without `design_system_path` key | Agents treat missing key as `null` (convention detection) | Agents error on missing key |

### Cal Brain-Search DoR

| ID | Category | Description | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| T-0040-026 | Happy path | Brain available; Cal invoked for a new feature ADR | Cal calls `agent_search` with domain-relevant terms before design work; findings appear in DoR "Retro risks" | Cal skips brain search or starts design before searching |
| T-0040-027 | Happy path | Brain unavailable; Cal invoked for a new feature ADR | Cal reads `retro-lessons.md` AND greps `docs/architecture/` for related prior ADRs; findings appear in DoR "Retro risks" | Cal skips retro-lessons or prior ADR scan |
| T-0040-028 | Edge case | Brain available but returns no results for feature domain | Cal notes "No relevant prior decisions found" in DoR "Retro risks" | Cal silently omits the "Retro risks" field or leaves it empty |
| T-0040-029 | Failure | Cal produces an ADR without any institutional memory search step | ADR is incomplete -- DoR "Retro risks" is mandatory | Cal treats brain-search as optional and omits it |

**Test counts:** 29 total. 12 happy path, 9 failure, 8 edge case. Failure tests (9) >= happy path minimum requirement.

## Exact Prose Additions

### Sable-UX (Producer) -- `source/shared/agents/sable-ux.md`

Add to `<workflow>` section, before existing step 1:

```markdown
0. **Design system check.** Follow the detection and loading rules in
   `{config_dir}/references/design-system-loading.md`. Read `tokens.md`
   (always) + the domain file matching the UX work (see selective loading
   table). Record which files you loaded. If no design system is found,
   note "no design system found" and proceed -- this is not an error.
```

Add to `<constraints>`:

```markdown
- When a design system is loaded, reference its tokens (colors, spacing,
  typography, component patterns) in UX doc output. Do not invent values
  that contradict loaded tokens.
```

Add to `<output>`, inside the DoR section:

```markdown
**Design system:** [Loaded: file1.md, file2.md | No design system found]
```

### Sable (Reviewer) -- `source/shared/agents/sable.md`

Add to `<workflow>`, after step 1:

```markdown
1a. **Design system cross-reference.** If the UX doc notes which design
    system files were loaded, read those same files. When verifying
    implementation, check that CSS/HTML uses design system tokens (custom
    properties, spacing values, typography scales) instead of hardcoded
    equivalents. Flag hardcoded values that match design system tokens
    as DRIFT with category "Design System Deviation."
```

### Colby -- `source/shared/agents/colby.md`

Add to `<workflow>` Build Mode, after the existing first sentence:

```markdown
Check for design system: if Eva's `<read>` tag includes design system files,
they are already in your context. If no design system files appear in your
context, follow the detection rules in
`{config_dir}/references/design-system-loading.md`. Record loaded files in
your DoR.
```

Add to the UI Contract table in `<output>`:

```markdown
| Design system | [tokens.md + domain file, or "None"] |
```

Add to `<constraints>`:

```markdown
- When a design system is loaded, use its tokens (CSS custom properties,
  spacing values, typography) instead of hardcoded values. Reference SVG
  icons from `design-system/icons/` (or the configured path) directly --
  no format conversion.
```

### Cal -- `source/shared/agents/cal.md`

Add to `<workflow>`, as the first step before "ADR Production":

```markdown
## Institutional Memory Search (mandatory)

Before any design work, search for prior decisions that may affect this feature:

1. **Brain available** (check `pipeline-state.md` for `brain_available: true`):
   call `agent_search` with terms derived from the feature domain (feature name,
   affected modules, related concepts). Look for prior ADRs, retro lessons, and
   architectural decisions. Inject relevant findings into DoR "Retro risks" field.

2. **Brain unavailable**: read `{config_dir}/references/retro-lessons.md` in full.
   Additionally, grep `docs/architecture/` for prior ADRs mentioning the same
   domain, modules, or integration points as the current feature.

3. **Either path**: note relevant findings in DoR before proceeding. "No relevant
   prior decisions found" is a valid finding -- silence is not.
```

## Contract Boundaries

| Producer | Shape | Consumer |
|---|---|---|
| `pipeline-config.json` | `{ "design_system_path": string \| null }` | Sable-ux, Colby, `/load-design` skill |
| Sable-ux output | `**Design system:** [Loaded: file1.md, file2.md]` annotation | Eva (extracts for Colby invocation), Sable (reviewer) |
| Eva invocation `<read>` | Design system file paths in `<read>` list | Colby |
| `design-system-loading.md` reference | Detection order, loading table, icon rules (prose) | Sable-ux, Colby |
| `/load-design` skill | Writes `design_system_path` to `pipeline-config.json` | All consuming agents (indirect) |

## Wiring Coverage

| Producer | Shape | Consumer | Step |
|---|---|---|---|
| `pipeline-config.json` template | `"design_system_path": null` | Agent detection logic (Sable-ux, Colby) | Step 1 -> Steps 2, 4 |
| `design-system-loading.md` | Prose reference doc | Sable-ux `<constraints>`, Colby `<constraints>` | Step 1 -> Steps 2, 4 |
| Sable-ux output annotation | `**Design system:** [list]` | Eva `<read>` list assembly -> Colby | Step 2 -> Step 4 |
| Sable-ux output annotation | `**Design system:** [list]` | Sable reviewer verification | Step 2 -> Step 3 |
| `/load-design` skill | Writes to `pipeline-config.json` | Detection logic in Sable-ux, Colby | Step 5 -> Steps 2, 4 |

No orphan producers. Every producer has at least one consumer in the same or earlier step.

## Data Sensitivity

| Method/Key | Classification | Rationale |
|---|---|---|
| `design_system_path` (pipeline-config.json) | `public-safe` | File path, no credentials |
| Design system file contents | `public-safe` | Design tokens are public project assets |
| `/load-design` skill | `public-safe` | Writes a file path to config, no auth |

## UI Specification

No UI surfaces are created or modified by this ADR. All changes are to agent persona prose and pipeline configuration. N/A.

## Notes for Colby

1. **All edits are in `source/shared/`.** Never edit `.claude/` directly. After Ellis commits, run `/pipeline-setup` to sync.

2. **The `design-system-loading.md` reference doc is the single source of truth for loading rules.** Agent personas reference it. Do not duplicate the loading table in multiple agent files -- point them at the reference doc.

3. **Prose additions, not code.** This ADR modifies agent behavior through prose in persona files. There are no functions to write, no hooks to create, no scripts to add. The "implementation" is writing precise Markdown into the right sections of the right files.

4. **The pipeline-config.json template is a state-guarded file.** Pipeline-setup does not overwrite it if it already exists. The `design_system_path` key will appear in new installations but NOT in existing ones. Agents must treat a missing key as `null` (graceful absence per T-0040-025).

5. **Relevant retro patterns:** Lessons 005 (Frontend Wiring Omission) and 006 (Frontend Layout Physics Gap) -- both show that cross-agent data contracts transmitted via `<constraints>` do not survive subagent context window boundaries. The design system file list is a cross-agent data contract. Sable-ux produces it, Eva propagates it via `<read>` (not `<constraints>`), Colby consumes it. The `<read>` tag is mechanical: it populates the context window before execution. If Eva's `<read>` list assembly fails, Colby falls back to re-detection (safe but redundant). The DoR UI Contract row ("Design system") makes the contract visible in Colby's output.

6. **Step ordering rationale:** Step 1 creates the reference doc that Steps 2-4 reference. Step 3 (Sable reviewer) depends on Step 2 (Sable-ux) because the reviewer reads the annotation the producer creates. Step 4 (Colby) depends on Steps 1-2 (reference doc + Sable output format). Step 5 (skill) is independent but placed last because it is the least-common path. Step 6 (Cal brain-search) is independent of Steps 1-5 and can be implemented in any order.

7. **Cal's brain-search step is unconditional.** It applies to every ADR Cal produces, not just design system work. The prose addition goes in Cal's `<workflow>` section, before "ADR Production." The step has two code paths (brain available vs. unavailable) -- both must produce output in the DoR "Retro risks" field. "No relevant prior decisions found" is a valid output; silence is not.

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | Auto-detect `design-system/` at project root | Done | Detection order in Decision section; T-0040-001 |
| 2 | Design files in PROJECT root, not `.claude/` | Done | Decision section: "Reference in place, do not copy" |
| 3 | Reference in place, path override only | Done | Pipeline Config Schema section; `/load-design` spec |
| 4 | Selective loading with domain-specific files | Done | Selective Loading Rules table; T-0040-007 through T-0040-011 |
| 5 | `/load-design` skill spec | Done | Skill specification with inputs/behavior/output/errors |
| 6 | SVG icons stay as SVG | Done | Icon Handling section; T-0040-022 |
| 7 | Graceful absence | Done | Detection Order step 3; T-0040-003 |
| 8 | Sable annotates loaded files | Done | Exact Prose: Sable-UX output annotation; T-0040-013 |
| 9 | Colby loads same files as Sable via `<read>` | Done | Cross-Agent Consistency section (amended); T-0040-012, T-0040-014a |
| 10 | Loading logic in prose, not script | Done | Implementation Plan: all steps are prose modifications |
| 11 | Colby references SVGs directly | Done | Exact Prose: Colby constraints; T-0040-022 |
| 12 | All edits in `source/` | Done | Implementation Plan file paths; Notes for Colby #1 |
| 13 | Cross-agent propagation uses `<read>` not `<constraints>` | Done | Cross-Agent Consistency section (retro lessons 005/006); T-0040-014a |
| 14 | Cal brain-search DoR step (mandatory) | Done | Step 6; Exact Prose: Cal section; T-0040-026 through T-0040-029 |

**Grep check:** TODO/FIXME/HACK/XXX in this ADR -> 0
**Template:** All sections filled -- no TBD, no placeholders
