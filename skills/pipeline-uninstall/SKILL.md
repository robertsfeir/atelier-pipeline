---
name: pipeline-uninstall
description: Use when users want to remove the atelier-pipeline multi-agent orchestration system from their project. Cleanly removes all installed files, hook registrations, and CLAUDE.md pipeline section. Preserves user-created custom agents and retro lessons on request.
---

# Atelier Pipeline -- Uninstall

This skill removes the Atelier Pipeline multi-agent orchestration system from the user's project. It is careful, transparent, and non-destructive by default.

<procedure id="uninstall">

## Uninstall Procedure

### Step 1: Inventory Installed Files

Before removing anything, scan the project to build a complete inventory of what was installed by the pipeline.

**Core pipeline files (installed by pipeline-setup):**

```
.claude/rules/
  default-persona.md
  agent-system.md
  pipeline-orchestration.md
  pipeline-models.md
  branch-lifecycle.md

.claude/agents/  (core agents only)
  sarah.md
  colby.md
  robert.md
  sable.md
  investigator.md
  distillator.md
  ellis.md
  agatha.md
  sentinel.md          (if Sentinel was enabled)

.claude/commands/
  pm.md
  ux.md
  architect.md
  debug.md
  pipeline.md
  devops.md
  docs.md

.claude/references/
  dor-dod.md
  retro-lessons.md
  invocation-templates.md
  pipeline-operations.md
  agent-preamble.md
  qa-checks.md
  branch-mr-mode.md
  xml-prompt-schema.md

.claude/hooks/
  enforce-paths.sh
  enforce-sequencing.sh
  enforce-pipeline-activation.sh
  enforce-git.sh
  session-hydrate.sh
  pre-compact.sh
  enforcement-config.json

.claude/pipeline-config.json
.claude/.atelier-version

docs/pipeline/
  pipeline-state.md
  context-brief.md
  error-patterns.md
  investigation-ledger.md
  last-qa-report.md
```

**Detect each file's existence** using Glob and build three lists:

1. **Core pipeline files** -- files matching the manifest above that exist on disk
2. **User-created custom agents** -- any `.md` files in `.claude/agents/` whose YAML frontmatter `name` does NOT match a core agent (sarah, colby, ellis, agatha, robert, sable, investigator, distillator, sentinel)
3. **Retro lessons content** -- check if `.claude/references/retro-lessons.md` contains any content beyond the empty template markers

### Step 2: Present Removal Plan

Display the full removal plan to the user BEFORE touching any files. Organize by category:

```
Pipeline Uninstall Plan
=======================

WILL REMOVE (core pipeline files):
  .claude/rules/           -- [N] files (Eva persona, orchestration rules, models, branch lifecycle)
  .claude/agents/          -- [N] core agent files (sarah, colby, ...)
  .claude/commands/        -- [N] files (slash command definitions)
  .claude/references/      -- [N] files (quality framework, templates, operations)
  .claude/hooks/           -- [N] files (enforcement scripts and config)
  .claude/pipeline-config.json
  .claude/.atelier-version
  docs/pipeline/           -- [N] files (pipeline state, context, error patterns)

WILL MODIFY:
  .claude/settings.json    -- Remove hook registrations (PreToolUse, SubagentStop, PreCompact)
  CLAUDE.md                -- Remove "Pipeline System (Atelier Pipeline)" section

WILL PRESERVE (not removed):
  [List any user-created custom agents found in .claude/agents/]
  [If retro-lessons.md has content: "retro-lessons.md contains [N] lessons -- see Step 3"]
  [If no custom agents and retro-lessons is empty: "No user content to preserve."]

Total files to remove: [count]
Total files to modify: [count]
```

### Step 3: Handle Preservable Content

**Retro lessons:** If `.claude/references/retro-lessons.md` contains content beyond the empty template, ask the user:

> Your retro lessons file contains accumulated knowledge from past pipelines.
> Would you like to:
> 1. **Keep it** -- I'll copy it to `docs/retro-lessons-backup.md` before removing the pipeline
> 2. **Remove it** -- Delete it along with everything else

If the user chooses to keep it, copy the file to `docs/retro-lessons-backup.md` before proceeding with removal.

**Custom agents:** If user-created custom agents are found in `.claude/agents/`, inform the user:

> Found [N] custom agent(s) that were not installed by the pipeline:
> - [agent-name] -- [description from frontmatter]
>
> These will NOT be removed. They'll remain in `.claude/agents/` but won't
> function without the pipeline's orchestration rules. You can delete them
> manually if you no longer need them.

### Step 4: Get User Confirmation

Ask for explicit confirmation before proceeding:

> This will remove [N] files and modify [M] files. This cannot be undone
> (though git can restore them if they were committed).
>
> Proceed with uninstall? (yes/no)

**Do not proceed without explicit "yes" from the user.**

### Step 5: Remove Files

Execute the removal in this order:

1. **Remove hook registrations from `.claude/settings.json`:**
   - Read the current settings file
   - Remove the `PreToolUse` hook entries that reference `enforce-paths.sh`, `enforce-sequencing.sh`, `enforce-pipeline-activation.sh`, and `enforce-git.sh`
   - Remove the `SessionStart` hook entry that references `session-hydrate.sh`
   - Remove the `PreCompact` hook entry that references `pre-compact.sh`
   - If the `hooks` object is now empty, remove the `hooks` key entirely
   - If `settings.json` is now empty (`{}`), delete the file
   - Preserve any non-pipeline hook entries and other settings

2. **Remove the pipeline section from `CLAUDE.md`:**
   - Find and remove the section starting with `## Pipeline System (Atelier Pipeline)` through the end of that section (up to the next `##` heading or end of file)
   - If `CLAUDE.md` is now empty or contains only whitespace, delete the file
   - Preserve all other content in `CLAUDE.md`

3. **Remove core pipeline files** (skip any that don't exist):
   - Delete all files in `.claude/hooks/` that match the manifest
   - Delete all core agent files in `.claude/agents/` (preserve custom agents)
   - Delete all files in `.claude/commands/` that match the manifest
   - Delete all files in `.claude/references/` that match the manifest
   - Delete all files in `.claude/rules/` that match the manifest
   - Delete `.claude/pipeline-config.json`
   - Delete `.claude/.atelier-version`
   - Delete all files in `docs/pipeline/` that match the manifest

4. **Clean up empty directories:**
   - If `.claude/hooks/` is now empty, remove the directory
   - If `.claude/agents/` is now empty (no custom agents), remove the directory
   - If `.claude/commands/` is now empty, remove the directory
   - If `.claude/references/` is now empty, remove the directory
   - If `.claude/rules/` is now empty, remove the directory
   - If `docs/pipeline/` is now empty, remove the directory
   - If `docs/` is now empty, remove the directory
   - Do NOT remove `.claude/` itself -- it may contain `settings.json` or other non-pipeline files

### Step 6: Print Summary

After removal, print a summary:

```
Atelier Pipeline uninstalled.

Removed: [N] files across [M] directories
Modified: .claude/settings.json (hooks removed), CLAUDE.md (pipeline section removed)
Preserved: [list of preserved items, or "nothing"]

The atelier-pipeline plugin is still registered with Claude Code.
To fully remove it: claude plugin remove atelier-pipeline

If you change your mind, reinstall with: /pipeline-setup
```

</procedure>

<gate id="uninstall-constraints">

## Important Notes

- **Never remove files without showing the plan first.** The inventory step is mandatory.
- **Never remove user-created custom agents.** Only remove files that match the core pipeline manifest.
- **Always offer to preserve retro-lessons.md.** This file accumulates institutional knowledge that may be valuable even after uninstalling.
- **Preserve non-pipeline content in settings.json and CLAUDE.md.** Only remove pipeline-specific entries.
- **Handle missing files gracefully.** If a file from the manifest doesn't exist, skip it silently -- don't error.
- **This skill does NOT remove the plugin itself.** It removes the installed project files. The user must run `claude plugin remove atelier-pipeline` separately to remove the plugin.
- **This skill does NOT remove the Atelier Brain database.** Brain data persists independently. If the user wants to remove brain data, they should use their database management tools directly.

</gate>

</SKILL.md>
