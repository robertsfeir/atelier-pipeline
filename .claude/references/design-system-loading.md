# Design System Loading Reference

This document is the single source of truth for design system detection, selective
loading, cross-agent consistency, and icon handling. Agent personas reference this
doc rather than duplicating the rules inline.

## Detection Order

When an agent begins work that touches UI, it must resolve the design system path
using this three-step detection order:

1. Read `design_system_path` from `pipeline-config.json`. If the value is non-null
   and non-empty, use that path as the design system directory. Config overrides
   convention -- if both a configured path and a `design-system/` directory at the
   project root exist, the configured path takes precedence.

2. Otherwise, check if `design-system/` exists at the project root. If it does,
   use that as the design system directory.

3. If neither exists, proceed without a design system. No error, no warning beyond
   the agent-level annotation ("no design system found"). This is not a failure
   condition.

**Missing key:** If `design_system_path` is absent from `pipeline-config.json`
(pre-existing installs that predate ADR-0040), treat the missing key as null and
fall through to step 2. Agents must not crash on a missing key.

**tokens.md required:** Once a design system directory is resolved, check that
`tokens.md` exists inside it. If `tokens.md` is missing, log
"tokens.md not found at [path] -- proceeding without design system" and treat
the result as no design system found (step 3 behavior). Do not load other design
system files without `tokens.md`.

## Selective Loading Rules

When a design system is detected and `tokens.md` is confirmed present, load
`tokens.md` (always) plus one domain-specific file based on the work being done:

| Building... | Load |
|---|---|
| Any UI | `tokens.md` (always) |
| Components, forms | + `components.md` |
| Navigation | + `navigation.md` |
| Dashboards, data display | + `data-viz.md` |
| Marketing/web pages | + `layouts-web.md` |
| App screens | + `layouts-app.md` |

Domain file selection is based on the ADR step description or UX doc section being
worked on. If the description is ambiguous (no clear domain match), load
`components.md` as the default domain file.

**Missing domain file:** If the selected domain file does not exist at the resolved
path, log "design system file [name] not found -- proceeding without it" and
continue with `tokens.md` only. Do not crash or block.

## Cross-Agent Consistency

Sable-ux (producer) loads design system files during UX doc production and records
which files she loaded in her output as:

```
**Design system:** Loaded: tokens.md, components.md
```

or, when no design system was found:

```
**Design system:** No design system found
```

Eva extracts this annotation and passes the listed file paths in Colby's
invocation `<read>` tag (not `<constraints>`) to ensure consistency without
re-detection.

**Why `<read>` and not `<constraints>`:** Retro lessons 005 and 006 demonstrate
that behavioral constraints do not survive subagent context window boundaries.
`<read>` is mechanical -- it populates the agent's context window before execution
begins. `<constraints>` is prose the agent may deprioritize.

Sable (reviewer) reads the same design system files noted in the UX doc annotation
to verify implementation fidelity. She does NOT auto-detect independently.

If Eva omits design system files from Colby's `<read>` but `design-system/` exists
at the project root, Colby re-detects and loads the design system (redundant but
safe). The worst case is inconsistency, not failure.

## Icon Handling

Reference SVG files from `design-system/icons/` (or the configured path equivalent)
directly in generated HTML/CSS. No format conversion. The icon file names are the
icon vocabulary -- read the directory listing to discover available icons.

If `design-system/icons/` does not exist, proceed without icon references. Do not
create broken icon references or error on the absence.

## Expected Directory Structure

A valid design system directory contains at minimum:

```
design-system/
  tokens.md          # Required -- color, spacing, typography tokens
  components.md      # Optional -- component patterns and usage
  navigation.md      # Optional -- navigation conventions
  data-viz.md        # Optional -- data visualization guidelines
  layouts-web.md     # Optional -- marketing/web page layout patterns
  layouts-app.md     # Optional -- app screen layout patterns
  icons/             # Optional -- SVG icon assets
    *.svg
```

The directory may be at the project root (`design-system/`) or at any path
configured via `design_system_path` in `pipeline-config.json`.
