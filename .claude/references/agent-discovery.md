<!-- Part of atelier-pipeline. Agent discovery protocol — read at boot, evict after. -->

<section id="agent-discovery">

## Agent Discovery

Eva discovers custom agents at session boot by scanning `.claude/agents/` for
non-core persona files. Discovered agents are **additive only** -- they never
replace core agent routing.

### Core Agent Constant

The following 14 agents are hardcoded core agents. Any `.md` file in
`.claude/agents/` whose YAML frontmatter `name` field does not match one of
these names is a discovered agent:

```
cal, colby, roz, ellis, agatha, robert, robert-spec, sable, sable-ux, investigator, distillator, sentinel, darwin, deps
```

### Discovery Protocol

1. **Scan:** Run `Glob(".claude/agents/*.md")` to list all agent files.
2. **Read frontmatter:** For each file, read the YAML frontmatter `name` field.
3. **Compare:** If the `name` does not match any core agent constant, it is a
   discovered agent. Read its `description` field.
4. **Announce:** "Discovered N custom agent(s): [name] -- [description]." If
   zero non-core agents found, no announcement (or "No custom agents found.").
5. **Error handling:** If the scan fails (Glob error, file read error), log:
   "Agent discovery scan failed: [reason]. Proceeding with core agents only."
   Never block session boot on a discovery error.

### Conflict Detection

When Eva detects a discovered agent whose description overlaps with a core
agent's domain (same intent category in the auto-routing table):

1. Eva announces the conflict: "This could go to [core agent] (core) or
   [discovered agent] (custom). Which do you prefer for [intent]?"
2. Eva asks the user **once per (intent, agent) pair per session**.
3. The user's choice is recorded (see Brain Persistence below).
4. On subsequent messages with the same intent pattern, Eva uses the recorded
   preference without re-asking.
5. Discovered agents with **no description overlap** are available only via
   explicit name mention (e.g., "ask [agent-name] about this").

Discovered agents **never shadow** core agents without explicit user consent.
Core routing table is always checked first.

### Brain Persistence for Routing Preferences

- **Brain available:** Eva captures the preference via `agent_capture` with
  `thought_type: 'preference'`, `source_agent: 'eva'`, metadata includes
  `routing_rule: {intent} -> {chosen_agent}`. On subsequent sessions, Eva
  queries brain for existing routing preferences before asking.
- **Brain unavailable:** Eva records the preference in `context-brief.md`
  under "## Routing Preferences". Preference is session-scoped -- lost on
  next session, re-asked.

See `.claude/commands/create-agent.md` for the inline agent creation protocol.

</section>
