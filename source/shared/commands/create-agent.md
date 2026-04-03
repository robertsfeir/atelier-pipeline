# Inline Agent Creation Protocol

When a user pastes markdown into the chat that contains an agent definition
pattern (identity/role description, behavioral rules, tool/constraint lists),
Eva recognizes it and offers conversion.

## Detection Heuristic

Eva identifies agent-like content when pasted markdown contains **two or more**
of: a role or identity statement, behavioral rules or guidelines, a tool or
capability list, constraint or boundary definitions, an output format
specification. Eva asks: "This looks like an agent definition. Want me to
convert it to a pipeline agent?"

## Conversion Process

1. **Parse** the content structure, mapping sections to XML tags.
2. **Prepare** the converted version following `{config_dir}/references/xml-prompt-schema.md`
   tag vocabulary:
   - **YAML frontmatter:** `name` (kebab-case from agent name), `description`
     (one-line from identity), `disallowedTools` (conservative default:
     `Agent, Write, Edit, MultiEdit, NotebookEdit` -- read-only)
   - **Comment:** `<!-- Part of atelier-pipeline. -->`
   - **`<identity>`** from the agent's role/identity text
   - **`<required-actions>`** with reference to `{config_dir}/references/agent-preamble.md`
     plus any agent-specific actions from the source material
   - **`<workflow>`** from the agent's process/steps (omit tag entirely if
     source has no workflow content)
   - **`<examples>`** from the agent's examples (omit tag entirely if none)
   - **`<tools>`** listing the agent's tool access
   - **`<constraints>`** from the agent's rules/boundaries
   - **`<output>`** from the agent's output format (if absent, use a minimal
     default: "Produce structured output with DoR and DoD sections.")
3. **Name collision check:** If the parsed name matches a core agent constant,
   Eva rejects: "[name] conflicts with a core agent. Choose a different name."
4. **Present** the converted content to the user for approval before writing.
5. **Write via Colby:** Eva invokes Colby with explicit task: "Write this file
   to `{config_dir}/agents/{name}.md`" with the full content in the CONTEXT field.
   Eva does **NOT** write the file herself -- this is a mandatory routing to
   Colby.
6. **If user declines:** No file is written. Eva acknowledges and moves on.
7. **Post-write discovery:** Eva re-runs the discovery scan to register the
   new agent immediately.
8. **Enforcement note:** Eva announces: "[agent-name] has read-only access by
   default. To grant write access, add a case to `{config_dir}/hooks/enforce-paths.sh`."
