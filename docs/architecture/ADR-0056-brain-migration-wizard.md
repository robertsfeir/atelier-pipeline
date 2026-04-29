# ADR-0056: Brain Migration Wizard (Phase 3 of ADR-0055)

## Status
Accepted. Implements Phase 3 of ADR-0055. ADR-0055 remains the parent decision; this ADR is scoped to the one-time migration step that runs inside `pipeline-setup` when an existing bundled-brain install is detected. Both ADRs are valid concurrently — ADR-0055 sets the architectural target, ADR-0056 specifies how an existing user gets there without losing data.

## Context
Phase 1 of ADR-0055 shipped the suffix-match clear hook and `.brain-not-installed` sentinel; Phase 2 merged the atelier-brain feature set into the standalone mybrain plugin (mybrain commit `d3abecb`, 15 behavioral tests passing, additive `schema_migrations` v1-to-merged migration validated). Phase 3 deletes `brain/` and the `brain-setup` skill from atelier-pipeline.

Existing installs sit in a state we deliberately created in Phase 1: a working `brain/` server, an old `permissions.allow` block prefixed `mcp__plugin_atelier-pipeline_atelier-brain__`, a `.claude/brain-config.json` whose key shape happens to be **already compatible** with mybrain (both ship `database_url`, `scope`, `brain_name`, `openrouter_api_key`, and the ADR-0054 multi-provider fields under identical names — confirmed by reading `mybrain/lib/config.mjs`), and an `ATELIER_BRAIN_DB_PASSWORD` env var that mybrain neither requires nor forbids since `database_url` is what the server actually consumes. The migration is therefore *less* a translation than a hand-off: same DB, same data, same config keys, different MCP server registration.

Phase 1's `pipeline-setup` Step 0e already strips the stale `permissions.allow` prefix unconditionally on every run, so that piece is done. What is missing is the plumbing that takes a user from "old brain still bundled" to "mybrain installed against the same database, brain working" — with a backup gate, a rollback inventory, a multi-project warning, and an explicit "start fresh" exit. The product owner described seven steps; the architect review added five guardrails. This ADR commits to the wizard's shape.

The mybrain bundled-mode `docker-entrypoint.sh` table-name guard (`thought_links` vs `thought_relations`) is a real bug, but it lives in mybrain and runs only on bundled-mode container restarts. It does not corrupt anything — it re-applies `schema.sql` idempotently. The wizard does not need to work around it; mybrain's owner fixes it in mybrain.

## Options Considered

**Option A: Manual migration documented in CHANGELOG.** Cheapest. We ship Phase 3 with a "here is what to do" prose section: stop old brain, install mybrain, point it at the same DB. Rejected because the load-bearing detail is the **point of no return** — once `brain/` is gone from the user's plugin, a confused user has no obvious path back. The whole point of ADR-0055's three-phase rollout is to never silently break an existing install.

**Option B: Dedicated migration wizard inside `pipeline-setup` (this ADR).** A new step in `pipeline-setup` that detects the legacy install, presents a plan, takes an explicit consent, performs `pg_dump` if available, removes the bundled brain, installs mybrain, runs the additive schema migration, and verifies health. Each transition is a named state with a recovery action. The cost is real (one more wizard step in a skill that already has eight cleanup steps) but bounded. Selected.

**Option C: Side-channel migration script (`scripts/migrate-brain.sh`).** A standalone script the user runs manually after upgrading the plugin. Cleaner separation of concerns. Rejected because it requires a second user action (run the plugin upgrade, *then remember* to run the script) and we have no way to make the second action mandatory. Users skip optional scripts; the failure mode is "your brain stopped working and you don't know why."

## Decision
Phase 3 of ADR-0055 ships a migration wizard inserted as a new step (between the existing Step 0e cleanup and the `brain-setup` invocation) in `pipeline-setup`. The wizard runs at most once per install — once mybrain is registered, the legacy detection signal is absent and the step is a silent no-op. The wizard offers two paths: **migrate** (preserve existing data; run the additive schema migration; reuse the same DB) and **start fresh** (wipe and start a brand new mybrain install). Both paths converge on a verified-healthy mybrain.

The wizard treats `pg_dump` as **advisory blocking**: if `pg_dump` is on PATH and the DB is reachable, take the backup before any destructive step and refuse to proceed if the dump fails. If `pg_dump` is unavailable (remote DB without local pg tools), surface the gap loudly, show the manual `pg_dump` command, and require an explicit "I have my own backup" acknowledgement before continuing. Backup is never silently skipped.

Colby writes a behavioral test for the wizard's idempotency — running `pipeline-setup` twice on a freshly migrated install must result in the wizard being a no-op the second time, because a re-trigger after partial migration is the failure mode that produces double-removed brain plugins. Colby also writes a behavioral test for the rollback contract on the highest-risk transition (state S5 below: schema migration failure post-install) because that is the state where the user has a removed old brain, an installed new brain, and a half-migrated DB — silent failure here is unrecoverable without operator intervention.

### Detection Signals

The wizard triggers when **all three** of the following hold (AND, not OR — any single signal can produce false positives in long-lived projects):

1. The plugin's own `mybrain` MCP registration is **absent** from the runtime tool list (Eva probes via ToolSearch; if any `mcp__*__mybrain__*` or equivalent mybrain-prefixed tool resolves, the user is already on mybrain).
2. A `.claude/brain-config.json` exists whose `database_url` references a reachable Postgres instance (the wizard tests reachability with a single `SELECT 1` before declaring "old brain").
3. The bundled-brain artifact is present in the user's plugin install — specifically, `${CLAUDE_PLUGIN_ROOT}/brain/server.mjs` is readable. Phase 3 deletes this file from the source tree, so its presence in the user's `${CLAUDE_PLUGIN_ROOT}` indicates the user has not yet upgraded past Phase 3 OR has a stale install — both cases the wizard should handle.

Signal 3 is the version discrimination mechanism. Once the user has upgraded to a Phase-3-or-later plugin release, `${CLAUDE_PLUGIN_ROOT}/brain/server.mjs` no longer exists in the source tree. If it is still present in the user's install, they are on the upgrade boundary — exactly when the wizard should run.

### Wizard State Machine

| State | Action | On success → next state | On failure → recovery action |
|-------|--------|-------------------------|-------------------------------|
| **S0** Detect | Run the three signals above; if any fails, skip wizard entirely (silent no-op). | → S1 if all three match; → END (silent) otherwise | n/a |
| **S1** Inform & Consent | Present the plan: what will change, what data is preserved, the multi-project shared-DB warning, and the migrate vs. start-fresh fork. Require explicit consent for the chosen path. | → S2 (migrate path) or → S2-fresh (fresh path) | User declines → END with no changes; print "Wizard cancelled. Re-run /pipeline-setup to revisit." |
| **S2** Backup | If `pg_dump` available + DB reachable → take dump to `~/.atelier-brain-backup-{timestamp}.sql`. Else surface manual command and require `--i-have-my-own-backup` acknowledgement. | → S3 | Dump command failed → HALT; print backup path attempt + error; user retries or cancels. **No state change yet — old brain still installed.** |
| **S2-fresh** Backup (fresh path) | Same as S2 but with explicit "this backup will let you restore IF you change your mind" framing. | → S3-fresh | Same as S2 |
| **S3** Stop & Remove Old Brain | Stop any running bundled-mode container (if Docker strategy detected). Do **not** drop tables. Do **not** remove `.claude/brain-config.json`. Do **not** remove `ATELIER_BRAIN_DB_PASSWORD` env var. Remove only the bundled `brain/` artifact references the user controls (the `brain/` source tree is removed by the plugin upgrade itself, not by the wizard). | → S4 | Container stop failed → HALT with `docker compose down` instructions. User can manually stop and resume the wizard. |
| **S3-fresh** Drop Schema | Run `DROP SCHEMA public CASCADE; CREATE SCHEMA public;` against the existing DB after a final "are you sure" gate. | → S4-fresh | Drop failed → HALT; print error; user runs cleanup manually. Backup at S2-fresh is the fallback. |
| **S4** Install mybrain | Print the install command for the user to run (`claude plugin install <mybrain-source>`); the wizard cannot install plugins on the user's behalf. Wait for user confirmation that mybrain is registered. Probe ToolSearch to verify. | → S5 | Probe fails → HALT with diagnostic; user installs mybrain manually and re-runs `/pipeline-setup`. The wizard's idempotency test (above) covers the re-run case. |
| **S4-fresh** Install mybrain | Same as S4. | → S5-fresh | Same as S4. |
| **S5** Verify & Migrate Schema | Mybrain server starts on its own; `runMigrations()` applies the additive v1→merged migration on first connect. Wizard probes `/health` and runs `atelier_stats`. | → S6 (clear sentinels, success) | Schema migration failed → HALT with backup-restore instructions. **This is the highest-risk state** — old brain is gone, new brain is installed, DB is in a partial migration state. Recovery: `psql … < ~/.atelier-brain-backup-{timestamp}.sql` plus mybrain version pin guidance. |
| **S5-fresh** Verify | Same as S5 but the DB is empty so `runMigrations()` is a fresh apply. | → S6-fresh | Health probe failed → HALT with mybrain config hand-off (`/brain-setup` from the new plugin). |
| **S6** Clear Sentinels & Confirm | Remove `.brain-not-installed` and `.brain-unavailable` if present. Run a final round-trip `agent_capture` + `agent_search`. Print success summary including backup path. | → END (success) | Round-trip failed → soft warning, leave wizard "incomplete" marker; pipeline still works because brain is non-blocking per ADR-0053. |

### Config Key Migration Map

`mybrain/lib/config.mjs` accepts every key the atelier-brain `brain-config.json` writes. The migration is preservation, not translation. The wizard rewrites no config keys.

| Old key (atelier-brain `.claude/brain-config.json`) | New key (mybrain `brain-config.json`) | Action |
|------------------------------------------------------|----------------------------------------|--------|
| `database_url` | `database_url` | preserve |
| `scope` | `scope` | preserve |
| `brain_name` | `brain_name` | preserve (default in mybrain becomes `"mybrain"` if absent; the wizard does not overwrite an existing value) |
| `openrouter_api_key` | `openrouter_api_key` | preserve |
| `embedding_provider` / `embedding_model` / `embedding_api_key` / `embedding_base_url` | identical | preserve |
| `chat_provider` / `chat_model` / `chat_api_key` / `chat_base_url` | identical | preserve |
| (none — env var) `ATELIER_BRAIN_DB_PASSWORD` | (none — same env var; `${ATELIER_BRAIN_DB_PASSWORD}` placeholder in `database_url` continues to resolve) | preserve env var; do **not** rename |

The only translation case is the `permissions.allow` block, which Phase 1's Step 0e already handles by stripping the stale prefix; mybrain's `brain-setup` re-adds the new-prefixed entries when the user runs it post-install (S4 above). The wizard does not touch `permissions.allow` directly — it relies on the existing Step 0e cleanup plus mybrain's own setup skill.

### Rollback Guarantee

At every destructive transition, the wizard tells the user **what state the install is in** and **the exact command to recover**. The contract:

- **Before S2 (consent stage):** "Nothing has changed. Cancel anytime."
- **After S2 (backup taken):** "Backup at `~/.atelier-brain-backup-{timestamp}.sql`. To restore: `psql {database_url} < {backup_path}`."
- **After S3 (old brain stopped):** "Old brain container stopped. Restart with `docker compose -f {old_compose_path} up -d` if you need to roll back. Backup still valid."
- **After S4 (mybrain installed):** "mybrain registered. To roll back: uninstall mybrain plugin, restore old brain from a previous plugin version, run `psql … < {backup_path}` if schema was migrated."
- **After S5 (schema migrated):** "Migration complete. Backup retained at {backup_path} for {N} days — delete manually when confident."
- **On any HALT:** Print the current state name (S0–S6), what succeeded, what failed, what the user should run to either resume or roll back.

The wizard never deletes the backup file. The user owns retention.

### Multi-Project Shared DB Warning

The S1 consent screen explicitly states: "If this Postgres database is used by other atelier-pipeline projects, the schema migration affects all of them. Migrating one project migrates the schema for every project pointing at this DB. Existing data is preserved (additive migration); new columns and tables are added; nothing is dropped." The user confirms understanding before S2 proceeds. This is a one-line gate — not a separate state — because the migration is additive and the warning is informational, not branching.

## Rationale
Option B beats A because the failure mode of A — a documented manual migration that users skip or botch — is the same failure mode ADR-0055's three-phase rollout was designed to prevent. Shipping Phase 3 without an in-skill wizard would invalidate the rationale for not collapsing Phases 1 and 3 in the first place.

Option B beats C because `pipeline-setup` is the skill users already run on plugin upgrade. Migration runs on the upgrade path the user is already taking; no second action is required, no second action can be skipped.

The "advisory blocking" stance on `pg_dump` is the load-bearing detail. Hard-blocking on missing `pg_dump` punishes remote-DB users (who legitimately don't have local pg tools). Silently skipping backup punishes the user who assumed there would be one. The "I have my own backup" acknowledgement keeps the user in the loop without forcing local tool installs.

The state machine has two parallel tracks (migrate vs. fresh) instead of a flag-driven single track because the recovery actions diverge — `S3-fresh` drops a schema, `S3` does not. Naming the states separately makes the rollback contract auditable.

If a user runs the wizard on a corrupted `.claude/brain-config.json` (malformed JSON), the detection signal 2 fails its reachability probe and the wizard exits silently at S0. The user falls through to the existing `brain-setup` invocation, which re-prompts. That is the right behavior — the wizard is opinionated about what "old brain" looks like and refuses to act on ambiguous state.

If the additive schema migration drops or renames a column (against current promise), all migrated installs lose data with no automated rollback path — revisit if mybrain's `migrations/` directory ever introduces a non-additive migration. The rollback then becomes manual `pg_dump` restore plus mybrain version pin, which is documented in the rollback contract.

Out of scope: changing how `brain-setup` itself works inside mybrain (mybrain owns its setup skill); fixing the `docker-entrypoint.sh` `thought_links` guard (mybrain owns it; idempotent re-apply is harmless); adding telemetry on wizard usage (Phase 4 if we ever care).

Rollback sketch: the wizard touches no schema directly except via mybrain's `runMigrations()`. Reverting Phase 3 is a git revert of the deletion commits in atelier-pipeline (restoring `brain/` and the brain-setup skill) plus, for any user already migrated, a manual `pg_dump` restore. The wizard's backup file is the user's insurance policy; the additive migration's `schema_migrations` ledger is the authoritative record of what was applied.

## Falsifiability
Revisit if any of the following hold:
- A user reports the wizard ran twice (idempotency violated) and either left them in a broken state or removed mybrain unintentionally.
- A user reports schema migration failure at S5 with no actionable rollback message — the rollback contract is the load-bearing piece and any state where the user does not know what to do is a contract failure.
- The "advisory blocking" `pg_dump` policy results in a measurable number of users (>1 reported case) skipping backup and then losing data — escalate to hard-block on missing `pg_dump`.
- Mybrain ships a non-additive migration and existing-install users lose data — revisit the migration contract entirely.
- Detection signal 3 (`brain/server.mjs` presence) produces false positives because some users vendor the brain into their own repo independently of the plugin.

## Sources
- `docs/architecture/ADR-0055-brain-pipeline-separation.md`
- `skills/pipeline-setup/SKILL.md` (Steps 0–0e cleanup chain; brain-setup invocation point)
- `skills/brain-setup/SKILL.md` (config key shape, ToolSearch schema preload)
- `skills/brain-uninstall/SKILL.md` (database-strategy detection patterns; per-strategy teardown commands)
- `/Users/sfeirr/projects/mybrain/lib/config.mjs` (config key compatibility with atelier-brain shape)
- `/Users/sfeirr/projects/mybrain/server.mjs` (`runMigrations()` invocation on startup)
- `/Users/sfeirr/projects/mybrain/package.json` (package name `mybrain` v1.0.0)
