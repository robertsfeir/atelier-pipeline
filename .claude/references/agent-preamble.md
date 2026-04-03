# Agent Preamble -- Shared Required Actions

<!-- Part of atelier-pipeline. Read by all agents at the start of every work unit. -->
<!-- CONFIGURE: .claude = IDE config directory (.claude for Claude Code, .cursor for Cursor) -->

Every agent follows these steps at the start and end of every work unit.
Agent-specific cognitive directives and domain-specific actions remain in
each agent's persona file.

<preamble id="shared-actions">

## Standard Required Actions

1. **DoR first.** Extract requirements from upstream artifacts into a table
   with source citations per `.claude/references/dor-dod.md`. If an upstream
   artifact referenced in your DoR was not in your READ list, note it.

2. **Read upstream artifacts and prove it.** Extract every functional
   requirement, edge case, and acceptance criterion. If the artifact is
   vague, note it in DoR rather than silently interpreting.

3. **Review retro lessons** from `.claude/references/retro-lessons.md`.
   Note relevant lessons in DoR under "Retro risks."

4. **Review brain context** if provided in your invocation via the
   `<brain-context>` tag. Check for relevant prior decisions, patterns,
   and lessons. Factor them into your approach. Agents with brain access
   (`mcpServers: atelier-brain` -- Cal, Colby, Roz, Agatha) also capture
   domain-specific knowledge directly via `agent_capture` per their Brain
   Access protocol. Agents without brain access surface knowledge in their
   output for Eva to capture on their behalf. (Agents operating under
   information asymmetry constraints -- Poirot, Distillator -- skip this.)

5. **DoD last.** Coverage verification showing every DoR item with status
   Done or Deferred with explicit reason per `.claude/references/dor-dod.md`.

</preamble>
