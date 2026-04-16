---
name: load-design
description: Use when a project's design system lives outside the project root (e.g., a shared monorepo package, a sibling directory). Sets design_system_path in pipeline-config.json so all agents use the specified path instead of the default design-system/ convention.
---

# /load-design -- Design System Path Override

This skill sets the `design_system_path` override in `pipeline-config.json` for projects
whose design system lives outside the project root.

## Purpose

By default, agents look for a `design-system/` directory at the project root. Use this skill
when your design system lives elsewhere -- for example, a shared monorepo package or a
sibling directory.

## Usage

```
/load-design /path/to/design-system
/load-design reset
```

**Inputs:**
- `path` (required): Path to the design system directory. Absolute or relative to project root.
- Special value `reset`: clears the override and falls back to convention-based detection.

## Behavior

### Normal Path

1. **Validate:** Check that the path exists. If it does not exist:
   `Directory [path] not found.` Stop.

2. **Validate tokens.md:** Check that `tokens.md` exists inside the directory. If missing:
   `No tokens.md found at [path]. A valid design system must include tokens.md.` Stop.

3. **Read pipeline-config.json:** Read `.claude/pipeline-config.json`. If not found:
   `Pipeline not installed. Run /pipeline-setup first.` Stop.

4. **Set path:** Update `design_system_path` to the provided path (resolve to absolute if
   relative was given).

5. **Write:** Write the updated `pipeline-config.json` back to `.claude/pipeline-config.json`.

6. **List discovered files:** List all `.md` files found at the path and note whether an
   `icons/` directory is present.

**Output:**
```
Design system path set to [path]. Found: [list of .md files]. [icons/ directory present | No icons/ directory]
Agents will use this path for design system loading.
```

### Reset

When the user runs `/load-design reset`:

1. Read `.claude/pipeline-config.json`. If not found:
   `Pipeline not installed. Run /pipeline-setup first.` Stop.

2. Set `design_system_path` to `null` (not empty string, not key removal -- the key must
   remain present with a null value so agents treat it as "use convention detection").

3. Write the updated config back.

**Output:**
```
Design system path cleared. Agents will fall back to convention-based detection (design-system/ at project root).
```

## Error Cases

| Condition | Error Message |
|-----------|---------------|
| Path does not exist | `Directory [path] not found.` |
| Path exists but no `tokens.md` | `No tokens.md found at [path]. A valid design system must include tokens.md.` |
| `pipeline-config.json` not found | `Pipeline not installed. Run /pipeline-setup first.` |

## Notes

- The configured `design_system_path` takes precedence over the `design-system/` convention
  path when both exist.
- Agents read `design_system_path` from `pipeline-config.json` on every invocation; clearing
  it with `reset` takes effect on the next agent invocation.
- To verify the current setting, read `.claude/pipeline-config.json` and check the
  `design_system_path` value.
- See `{config_dir}/references/design-system-loading.md` for the full detection and
  loading rules that agents follow.
