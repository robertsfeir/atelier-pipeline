# ADR-0055: Separate the Atelier Brain into a standalone mybrain plugin

## Status
Accepted. Supersedes the bundled-brain architecture established in ADR-0001 and refined by ADR-0017, ADR-0051, ADR-0053, and ADR-0054. Those ADRs remain valid for the brain itself; what changes is where the brain lives and how the pipeline addresses it.

## Context
The Atelier Brain currently ships inside this repo at `brain/`, registered as the `atelier-brain` MCP server through `plugin.json`. A second brain plugin (`mybrain`) lives in a separate repo and serves a simpler personal-memory use case. The two have diverged: atelier-brain has the operational maturity (conflict detection, consolidation, TTL, relations, hydration, REST/UI, multi-provider per ADR-0054, captured_by tracking, schema_migrations), while mybrain has the deployment ergonomics (bundled Postgres+Ollama+MCP container, async storage worker, configurable embedding dimension, shell-wrapper auto-start, `/health` endpoint, simpler 4-mode installer).

The pipeline does not require the brain. ADR-0053 made brain capture mechanically gated, and the `.brain-unavailable` sentinel already lets the pipeline degrade gracefully when the brain is down. But the gate hooks are coupled to a specific MCP tool name (`mcp__plugin_atelier-pipeline_atelier-brain__agent_capture`) hardcoded in `clear-brain-capture-pending.sh` and replicated in the brain-setup skill's `permissions.allow` list. Plugin SessionStart hooks also run brain-only steps (`npm install --prefix brain/`, `hydrate-telemetry.mjs`) on every session regardless of whether the user wants the brain.

We want one brain, used by both pipeline users and personal-memory users, distributed as its own plugin. The pipeline must continue to work with no brain installed at all -- not just "installed but unreachable." See research brief in this pipeline's session for the full coupling inventory and feature diff.

## Options Considered

**Option A: Keep brain in atelier-pipeline; deprecate mybrain.** Lowest migration cost. Existing installs unchanged. But it forces personal-memory users to install the entire pipeline plugin and gives up mybrain's deployment ergonomics (bundled container, async storage, shell wrappers, configurable dim). It also leaves the tool-name coupling in place, which is fine until someone forks the brain and the assumption breaks. Rejected: the deployment-ergonomics gap is real user-visible value, and the coupling is a latent footgun.

**Option B: Merge into mybrain repo; pipeline depends on mybrain plugin.** Brain leaves this repo entirely. Pipeline gates become "brain-aware but not brain-coupled" -- they look for *any* `*__agent_capture` tool call, not a hardcoded name. Brain-setup skill is removed from atelier-pipeline; users install mybrain separately. Migration cost is real (existing installs must move) but bounded by a one-time setup wizard run. This unifies the two brains under the more operationally mature feature set while gaining mybrain's deployment ergonomics. Selected.

**Option C: Two brains forever, with a shared protocol.** Define a brain protocol (tool names, schema) and let both plugins implement it. Maximum flexibility, double the maintenance, two divergent codebases that drift the moment a feature lands in one and not the other. We have lived this; it is what produced the feature gap. Rejected.

## Decision
We separate the brain from atelier-pipeline by merging atelier-brain's feature set into the mybrain plugin repo, then removing `brain/` from this repo. Pipeline gate hooks are decoupled from the specific MCP server name. Existing installs migrate via a one-time setup wizard run.

The merged brain keeps every atelier-brain feature (conflict detection, consolidation, TTL, relations, hydration, REST/UI, multi-provider per ADR-0054, captured_by, schema_migrations, full thought_type / source_agent / source_phase enums, provenance fields) and adopts every mybrain ergonomic (bundled container mode, async storage worker, configurable embedding dimension via `{{EMBED_DIM}}`, shell wrappers, `/health` endpoint, 4-mode installer). When a feature exists in both, atelier-brain's implementation wins because it has the operational hardening. Where mybrain has the only implementation (bundled mode, async worker, shell wrappers), it ports forward unchanged.

The tool-name coupling is resolved by matching on a tool-name *suffix* (`__agent_capture`) rather than the full prefixed name. The PostToolUse clear hook fires on any MCP tool whose name ends in `__agent_capture`, regardless of which plugin or `claude mcp add` registration produced it. The brain's tool names (`agent_capture`, `agent_search`, `atelier_stats`, `atelier_browse`, `atelier_relation`, `atelier_trace`, `atelier_hydrate`, `atelier_hydrate_status`) become the protocol. Any brain implementing those names is a valid pipeline brain.

The migration path: a transitional release of atelier-pipeline keeps `brain/` in place but adds the suffix-matching hook and a `pipeline-setup` migration step that detects an old-prefix `permissions.allow` entry and rewrites it. The next release removes `brain/` and the brain-setup skill from atelier-pipeline; users install mybrain separately. Two releases, not one, because silent breakage of existing installs is the worst outcome.

When brain is not installed at all, the pipeline must not deadlock. The gate hook checks for the sentinel `.brain-unavailable` (existing) *and* a new sentinel `.brain-not-installed`, written by `pipeline-setup` when the user opts out of brain installation. Either sentinel makes the gate pass-through. The SubagentStop hook that writes `.pending-brain-capture.json` short-circuits when either sentinel is present, so no pending file is ever written that cannot be cleared.

Plugin SessionStart no longer runs `npm install --prefix brain/` or `hydrate-telemetry.mjs`. Those move to the mybrain plugin's own SessionStart. The atelier-pipeline `plugin.json` ships with no brain-specific lifecycle steps.

This is a three-phase rollout. **Phase 1** (this ADR's build scope): suffix-match the clear-hook, add `.brain-not-installed` sentinel, add the migration rewrite to pipeline-setup, and merge the atelier-brain feature set into mybrain. Phase 1 ships atelier-pipeline with `brain/` still present so existing installs keep working. **Phase 2**: cut a mybrain release with the merged feature set; document the install path; pipeline-setup learns to detect mybrain and offer to register it. **Phase 3**: remove `brain/` and brain-setup skill from atelier-pipeline. Each phase is a separate pipeline run with its own ADR-relative scope.

Colby writes a behavioral test for the suffix-match hook because a regression here silently disables the brain capture gate -- pending files would accumulate and the next agent invocation would block forever or pass through incorrectly depending on the failure mode. Colby also writes a behavioral test for the `.brain-not-installed` sentinel pass-through because deadlock under "brain never installed" is the P4 failure that motivates this ADR.

### Factual Claims
- `clear-brain-capture-pending.sh` matches a hardcoded tool name `mcp__plugin_atelier-pipeline_atelier-brain__agent_capture` and must be changed to suffix-match `__agent_capture`.
- `enforce-brain-capture-gate.sh` already honors `.brain-unavailable` and must additionally honor a new `.brain-not-installed` sentinel.
- `enforce-brain-capture-pending.sh` must short-circuit (write nothing) when either sentinel is present, otherwise pending files can be written that cannot be cleared.
- `brain-setup` skill writes 8 entries to `.claude/settings.json` `permissions.allow` with prefix `mcp__plugin_atelier-pipeline_atelier-brain__`; `pipeline-setup` must detect and rewrite these on migration.
- `plugin.json` SessionStart currently invokes `npm install --prefix brain/` and `hydrate-telemetry.mjs`; both must be removed in Phase 3.
- atelier-brain's `schema.sql` hardcodes embedding dimension 1536; the merged brain must adopt mybrain's `{{EMBED_DIM}}` template substitution.
- atelier-brain's thought_type, source_agent, and source_phase enums are supersets of mybrain's; the merged schema takes the supersets.
- atelier-brain's `match_thoughts_scored()` and mybrain's are functionally equivalent (formula `0.5*recency + 2.0*importance + 3.0*cosine`); either implementation is acceptable.
- atelier-brain has no `/health` HTTP endpoint; the merged brain must expose `GET /health` returning `{"status":"ok"}`.
- atelier-brain has no async storage worker; the merged brain must port mybrain's `MYBRAIN_ASYNC_STORAGE` worker (500ms poll, batch 8, max 5 attempts).
- `NODE_TLS_REJECT_UNAUTHORIZED=0` must remain in the brain server startup env per existing constraint.

### LOC Estimate
Phase 1 only: ~150 lines changed across ~6 files (3 hook scripts, brain-setup skill migration step, pipeline-setup migration step, one new sentinel touch path). Phases 2 and 3 are larger but out of scope for this ADR's immediate build.

## Rationale
Option B beats A because the deployment ergonomics gap is user-visible and the tool-name coupling is a latent footgun that we should retire while we are touching this code anyway. It beats C because the two-brain status quo is what produced the feature divergence in the first place; a "shared protocol" with two implementations is a maintenance tax we have already proven we will not pay.

The suffix-match resolution is the load-bearing detail. It changes the brain's relationship to the pipeline from "specific server" to "any server implementing the protocol," which is the correct relationship for a plugin boundary. The cost is one false-positive class: any unrelated MCP tool ending in `__agent_capture` would clear the pending file. We accept this because the tool-name namespace is small, we control both endpoints, and the alternative (configurable tool-name pattern) adds installer complexity for a hypothetical conflict.

The three-phase rollout exists because silently breaking existing installs is the failure mode we most want to avoid. Phase 1 ships compatible-by-default; Phase 2 introduces the new path; Phase 3 removes the old path. If we collapsed Phase 1 and Phase 3 into one release, every existing user's first session after upgrade would fail.

If the merged brain's async storage worker drops embeddings under load, repeat readers see degraded search recall until backfill catches up -- revisit if `embedding IS NULL` rows accumulate beyond the worker's drain rate during normal pipeline use.

Rollback sketch: schema is additive in Phase 1 (new sentinel file, suffix-match hook). Reverting Phase 1 is a hook-script revert plus deleting the sentinel paths -- no DB migration. Phase 3 is destructive (removing `brain/`); rollback there is a git revert of the deletion commit, plus pointing users back to the in-repo brain. Phase 2 (mybrain release) lives in a separate repo and rolls back independently via mybrain version pinning.

Out of scope: changing the thought schema, changing the search formula, or altering ADR-0054's multi-provider model. This ADR is about *where the brain lives*, not *what it does*.

## Falsifiability
Revisit if any of the following hold:
- A pipeline user reports the brain capture gate firing on the wrong tool because the suffix `__agent_capture` collided with an unrelated MCP server.
- After Phase 3, an existing-install user's pipeline deadlocks because the migration step did not rewrite their `permissions.allow` and the sentinel logic did not catch the case.
- The merged mybrain release lags atelier-pipeline by more than one pipeline cycle on a feature that pipeline agents need (e.g., a new `source_phase` enum value), proving the plugin boundary is too high-friction for fast iteration.
- The async storage worker's null-embedding backlog ever exceeds, in a normal pipeline session, the worker's drain rate -- meaning ergonomics chosen for personal-memory use don't scale to pipeline use.

## Sources
- `brain/` (atelier-brain v1.3.1, server.mjs + lib/)
- `source/claude/hooks/enforce-brain-capture-gate.sh`
- `source/claude/hooks/enforce-brain-capture-pending.sh`
- `source/claude/hooks/clear-brain-capture-pending.sh`
- `source/claude/hooks/prompt-brain-prefetch.sh`
- `skills/brain-setup/SKILL.md`
- `plugin.json` (SessionStart hooks; mcpServers.atelier-brain entry)
- ADR-0001 (original brain architecture), ADR-0017 (brain hardening), ADR-0051 (brain trust hardening), ADR-0053 (mechanical brain capture gate), ADR-0054 (multi-provider LLM)
- mybrain repo (`templates/server.mjs`, bundled-mode compose, shell wrappers, `MYBRAIN_ASYNC_STORAGE` worker)
