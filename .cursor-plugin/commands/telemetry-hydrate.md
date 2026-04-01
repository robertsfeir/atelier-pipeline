---
name: telemetry-hydrate
description: Capture per-agent telemetry from Claude Code session files into the brain. Run manually or let the SessionStart hook handle it automatically.
---

<!-- Part of atelier-pipeline. Customize project-specific values in CLAUDE.md -->

<identity>
This is the telemetry hydration flow -- Eva runs the hydration script to capture
per-agent token usage, cost, and duration from Claude Code session JSONL files
into the brain database.
</identity>

<behavior>
When the user runs /telemetry-hydrate:

1. Check brain availability. If `brain_available: false` or brain is not configured,
   respond: "Brain is not configured. Run /brain-setup first." and stop.

2. Construct the project sessions path from the current working directory:
   - Take `CLAUDE_PROJECT_DIR` (current working directory)
   - Replace each `/` with `-`
   - Strip the leading `-`
   - Prepend `~/.claude/projects/-`
   - Example: `/Users/alice/projects/myapp` becomes `~/.claude/projects/-Users-alice-projects-myapp`

3. Run the hydration script via Bash:
   ```
   node brain/scripts/hydrate-telemetry.mjs <constructed-path>
   ```
   Use `${CLAUDE_PLUGIN_ROOT}/brain/scripts/hydrate-telemetry.mjs` if the plugin root
   is available; otherwise use the relative path `brain/scripts/hydrate-telemetry.mjs`.

4. Report the summary output to the user verbatim.

5. If the script reports 0 new agents hydrated, say:
   "Telemetry is up to date -- no new data to hydrate."

6. If the script exits with an error (database connection failure, path not found, etc.),
   report the error to the user and suggest checking the brain configuration with /brain-setup.
</behavior>

<output>
The hydration summary line from the script output, e.g.:
"Hydrated N agents across M sessions. Total: X tokens, $Y."

If already up to date: "Telemetry is up to date -- no new data to hydrate."
</output>

<constraints>
- Never block on hydration errors -- this is an advisory operation.
- Do not re-run if the script completes successfully, even if 0 agents were hydrated.
- The SessionStart hook runs this automatically with --silent on each new session;
  /telemetry-hydrate is the manual, verbose equivalent.
</constraints>
