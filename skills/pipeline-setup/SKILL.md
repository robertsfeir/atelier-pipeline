---
name: pipeline-setup
description: Use when users want to install or set up the atelier-pipeline multi-agent orchestration system in their project. Bootstraps all agent personas, rules, commands, references, and pipeline state files. Works for new and existing projects.
---

# Atelier Pipeline -- Setup

This skill installs the full Atelier Pipeline multi-agent orchestration system into the user's project.

> **Heads-up (Claude Code < 2.1.89):** Agent persona frontmatter declares an `effort` field (values: `low`, `medium`, `high`, `xhigh`) in addition to `model`. Claude Code runtimes older than **2.1.89** ignore the `effort` field silently -- the pipeline still functions, but effort-based promotion signals are not honoured by the runtime. See **ADR-0041** for the full effort-tier model. If your team is on an older Claude Code build, either upgrade or treat the `effort` field as documentation-only. Cursor users: the `effort` field is passed through as metadata; refer to Cursor release notes for runtime support.

<contract>
  <requires>
    - `CLAUDE_PLUGIN_ROOT` (Claude Code) or `CURSOR_PROJECT_DIR` (Cursor) environment variable set by the runtime.
    - Plugin `source/` tree present at `${CLAUDE_PLUGIN_ROOT}/source/` (shared, claude, cursor overlays).
    - Write access to project root (`.claude/`, `docs/`, `CLAUDE.md`).
    - `jq` available on `PATH` for hook registration in `settings.json`.
  </requires>
  <produces>
    - `.claude/rules/`, `.claude/agents/`, `.claude/commands/`, `.claude/references/`, `.claude/hooks/` populated from source overlays.
    - `.claude/pipeline-config.json` with branching strategy, project name, and feature flags.
    - `.claude/settings.json` with hook registrations (PreToolUse, SubagentStart, SubagentStop, SessionStart, PreCompact, PostCompact, StopFailure).
    - `.claude/.atelier-version` plugin version marker.
    - `docs/pipeline/` state files (`pipeline-state.md`, `context-brief.md`, `error-patterns.md`, `investigation-ledger.md`).
    - `CLAUDE.md` with pipeline section appended.
    - Cursor only: `.cursor-plugin/rules/*.mdc` reference wrappers.
  </produces>
  <invalidates>
    - Any prior install's `.claude/rules/`, `.claude/agents/`, `.claude/commands/`, `.claude/references/`, and `.claude/hooks/` contents (overwritten from source on re-sync; live state files in `docs/pipeline/` and `.claude/pipeline-config.json` are preserved).
    - Deprecated `quality-gate.sh`, orphan brain-capture hooks, orphan `session-hydrate.sh` registration, and stale `atelier-brain` `.mcp.json` entries (Steps 0–0d).
  </invalidates>
</contract>

<procedure id="setup">

## Setup Procedure

### Where Files Are Installed

Before gathering project information, understand where the pipeline installs files and how they interact with your project:

| Location | What Goes There | Git Status | Shared With Team? |
|----------|----------------|------------|-------------------|
| `.claude/rules/` | Eva persona, orchestration rules, model selection, branch lifecycle | Project-local, committed to repo | Yes -- team members get the same pipeline rules |
| `.claude/agents/` | Agent persona files (Sarah, Colby, etc.) | Project-local, committed to repo | Yes -- consistent agent behavior across the team |
| `.claude/commands/` | Slash command definitions (/pm, /pipeline, etc.) | Project-local, committed to repo | Yes -- same commands available to all |
| `.claude/references/` | Quality framework, invocation templates | Project-local, committed to repo | Yes -- shared knowledge base |
| `.claude/hooks/` | Enforcement scripts (path, sequencing, git guards) | Project-local, committed to repo | Yes -- same guardrails for everyone |
| `.claude/pipeline-config.json` | Branching strategy, feature flags | Project-local, committed to repo | Yes -- team-wide configuration |
| `.claude/settings.json` | Hook registrations (tells Claude Code to run the hooks) | Project-local, committed to repo | Yes -- hooks activate for all team members |
| `docs/pipeline/` | Pipeline state, context brief, error patterns | Project-local, committed to repo | Yes -- session recovery works across machines |
| `CLAUDE.md` | Pipeline section appended to project instructions | Project-local, committed to repo | Yes -- Claude Code reads this automatically |

**Key points:**
- All installed files live inside the project directory -- nothing is written to `~/.claude/` or other user-level locations.
- Everything is designed to be committed to git so team members inherit the pipeline when they clone.
- The plugin itself (installed via `claude plugin add`) is user-level, but the project files it generates are project-level.
- To remove all installed files later, use the `/pipeline-uninstall` skill.

### Step 0: Clean Up Deprecated quality-gate.sh

Before gathering any project information, unconditionally run this cleanup on every /pipeline-setup invocation. It is silent unless it finds something to remove.

1. **Check file:** Check if `.claude/hooks/quality-gate.sh` exists. If found: delete the file. Note that removal occurred.
2. **Check settings.json:** Check if `.claude/settings.json` exists and contains a hook entry referencing `quality-gate.sh` in any command string across all hook event types (PreToolUse, SubagentStop, PreCompact, etc.). If found:
   - Parse the JSON. If the JSON is malformed or invalid, log a warning ("Warning: .claude/settings.json is malformed JSON -- skipping quality-gate.sh entry removal. Does not block setup.") and continue to step 3.
   - Remove the hook entry containing "quality-gate" from the command string.
   - If removing that entry leaves an empty hooks array for an event type, remove the event type entry entirely (no empty arrays left behind).
   - Write the updated JSON back to `.claude/settings.json`.
   - Note that removal occurred.
3. **Print notice (conditional):** If either artifact was found and removed: print exactly `Removed deprecated quality-gate.sh (see retro lesson #003).`
4. **Silent no-op:** If neither found: do nothing. No output.

**Edge case handling:**
- File exists but settings.json entry already removed: detect file, delete it, print notice. Check settings.json independently of file existence.
- settings.json has quality-gate.sh entry but file does not exist: detect entry in settings.json, remove it, print notice.
- Both found: remove both, print single notice (not two).
- Neither found: silent no-op.

This cleanup targets only quality-gate.sh entries. Other hook entries (enforce-eva-paths.sh, enforce-sequencing.sh, enforce-git.sh, etc.) are not affected.

### Step 0b: Clean Up Orphan Brain-Capture Hooks

Unconditionally run this cleanup on every /pipeline-setup invocation. Silent unless it finds something to remove.

1. **Check prompt-brain-capture.sh:** If `.claude/hooks/prompt-brain-capture.sh` exists, delete it with `rm -f .claude/hooks/prompt-brain-capture.sh`. Note that removal occurred.
2. **Check warn-brain-capture.sh:** If `.claude/hooks/warn-brain-capture.sh` exists, delete it with `rm -f .claude/hooks/warn-brain-capture.sh`. Note that removal occurred.
3. **Print notice (conditional):** If either file was found and removed: print exactly `Removed orphan brain-capture hooks (superseded by brain-extractor agent).`
4. **Silent no-op:** If neither found: do nothing. No output.

### Step 0c: Clean Up Orphan session-hydrate.sh Registration

Unconditionally run this cleanup on every /pipeline-setup invocation. Silent unless it finds something to remove.

`session-hydrate.sh` is now an intentional no-op (superseded by the `atelier_hydrate` MCP tool) and must NOT be registered in `.claude/settings.json`. Older installs may still have a registration entry.

1. **Check settings.json:** Check if `.claude/settings.json` exists and contains a hook entry whose command string contains exactly `session-hydrate.sh` (not `session-hydrate-enforcement.sh` or other similarly-named hooks) across all hook event types (SessionStart is the typical location). If found:
   - Parse the JSON. If the JSON is malformed or invalid, log a warning ("Warning: .claude/settings.json is malformed JSON -- skipping session-hydrate.sh entry removal. Does not block setup.") and continue to Step 1 (Gather Project Information).
   - Remove the hook entry containing "session-hydrate.sh" from the command string.
   - If removing that entry leaves an empty hooks array for an event type, remove the event type entry entirely (no empty arrays left behind).
   - Write the updated JSON back to `.claude/settings.json`.
   - Note that removal occurred.
2. **Print notice (conditional):** If the entry was found and removed: print exactly `Removed orphan session-hydrate.sh registration (intentional no-op, see source comment).`
3. **Silent no-op:** If not found: do nothing. No output.

**Note:** The `.claude/hooks/session-hydrate.sh` file itself is NOT deleted — it is re-copied by Step 3a as an intentional no-op backward-compatibility shim. Only the `settings.json` registration is removed.

This cleanup targets only session-hydrate.sh registrations. Other hook entries are not affected.

### Step 0d: Clean Up Orphan atelier-brain .mcp.json Entry

Unconditionally run this cleanup on every /pipeline-setup invocation. Silent unless it finds something to remove.

The Atelier Brain MCP server is now registered and managed entirely by the plugin. Older installs may have a stale project-level `.mcp.json` entry that must be removed.

1. **Check .mcp.json:** Check if `.mcp.json` exists in the project root and contains an "atelier-brain" key under the `mcpServers` object. If found, atomically remove atelier-brain and delete the file if mcpServers is empty. Run via Bash:

   ```bash
   python3 -c "
   import json, os
   p = '.mcp.json'
   if not os.path.exists(p): exit(0)
   try:
       d = json.load(open(p))
   except Exception:
       print('Warning: .mcp.json is malformed JSON -- skipping atelier-brain entry removal. Does not block setup.')
       exit(0)
   d.get('mcpServers', {}).pop('atelier-brain', None)
   if not d.get('mcpServers'):
       os.remove(p)
   else:
       json.dump(d, open(p, 'w'), indent=2)
   "
   ```

   Then run the safety-net check — if `.mcp.json` still exists with empty or absent `mcpServers`, delete it unconditionally:

   ```bash
   if [ -f .mcp.json ]; then python3 -c "import json,os,sys; d=json.load(open('.mcp.json')); sys.exit(0) if d.get('mcpServers') else os.remove('.mcp.json')" 2>/dev/null; fi
   ```

   Note that removal occurred.
2. **Print notice (conditional):** If the entry was found and removed: print exactly `Removed stale atelier-brain .mcp.json entry (now managed by plugin).`
3. **Silent no-op:** If not found: do nothing. No output.

This cleanup targets only atelier-brain entries. Other MCP server entries in `.mcp.json` are not affected.

### Step 0e: Migrate Stale Brain MCP `permissions.allow` Entries (ADR-0055)

Unconditionally run this cleanup on every /pipeline-setup invocation. Silent unless it finds something to remove.

Per ADR-0055, the brain is moving from this pipeline plugin into the standalone `mybrain` plugin. The 8 `permissions.allow` entries written by older `brain-setup` runs use the bundled-plugin prefix `mcp__plugin_atelier-pipeline_atelier-brain__`. After Phase 3 these entries no longer match any registered tool — they are dead weight. Removing them now is safe: when the user re-runs `/brain-setup` against the current brain plugin, the correct entries are re-added.

1. **Check settings.json:** Check if `.claude/settings.json` exists and contains any `permissions.allow` entry whose value starts with the prefix `mcp__plugin_atelier-pipeline_atelier-brain__`. If found:

   ```bash
   python3 -c "
   import json, os
   p = '.claude/settings.json'
   if not os.path.exists(p):
       exit(0)
   try:
       s = json.load(open(p))
   except json.JSONDecodeError:
       print('Warning: .claude/settings.json is malformed JSON -- skipping ADR-0055 brain permissions cleanup. Does not block setup.')
       exit(0)
   allow = (s.get('permissions') or {}).get('allow') or []
   stale_prefix = 'mcp__plugin_atelier-pipeline_atelier-brain__'
   keep = [t for t in allow if not (isinstance(t, str) and t.startswith(stale_prefix))]
   removed = len(allow) - len(keep)
   if removed:
       s.setdefault('permissions', {})['allow'] = keep
       json.dump(s, open(p, 'w'), indent=2)
       print(f'Removed {removed} stale brain permission entries (ADR-0055).')
   "
   ```

2. **Print notice (conditional):** The python snippet prints `Removed N stale brain permission entries (ADR-0055).` when it removes anything. Re-run `/brain-setup` after upgrading to the standalone brain plugin to re-add the correct entries.
3. **Silent no-op:** If no stale entries are found, the snippet prints nothing.

This cleanup targets only entries with the `mcp__plugin_atelier-pipeline_atelier-brain__` prefix. Other `permissions.allow` entries (e.g., `Edit`, `Bash(...)`, other plugins' MCP tools) are not affected.

### Step 0f: Brain Migration Wizard (ADR-0056)

This step is a **one-time** migration wizard for users who installed the brain when it was bundled inside this plugin (ADR-0055 Phase 1 / Phase 2). Phase 3 deletes `brain/` from the plugin tree and moves the brain into the standalone `mybrain` plugin. The wizard hands the user from the old bundled brain to mybrain without losing data, or — if the user prefers — wipes the existing database and starts fresh against mybrain.

The wizard runs **at most once per install**. After a successful migration, the detection signals no longer match and Step 0f is a silent no-op on every subsequent `/pipeline-setup` invocation. Idempotency is the load-bearing contract — running this skill twice on a freshly migrated install must NOT re-trigger any destructive action.

#### S0 — Detect

Run all three detection signals silently. The wizard activates **only when all three** are true (logical AND, not OR — any single signal alone produces false positives in long-lived projects).

1. **mybrain is absent from the runtime tool registry.** Probe ToolSearch for any tool whose name matches the pattern `mcp__*mybrain*` or `mcp__*atelier-brain__*` (the suffix-match pattern from ADR-0055 Phase 1). If any matching tool resolves, the user is already on mybrain (or some compatible brain) — exit Step 0f silently.
2. **A `.claude/brain-config.json` exists whose `database_url` references a reachable Postgres instance.** Read the file (use the same `python3 -c "import json; print(json.dumps(json.load(open('.claude/brain-config.json'))))"` pattern used by `/brain-setup` Path A). If absent or malformed, exit Step 0f silently. Otherwise, expand `${ENV_VAR}` placeholders against the current environment and run a `SELECT 1` reachability probe via `psql "<expanded_url>" -c "SELECT 1;"` (timeout 5s). If the probe fails, exit Step 0f silently — the wizard refuses to act on ambiguous state. Use the brain-uninstall skill's database-strategy detection logic to classify the URL as Docker / Local / Remote (this is needed in S3 below).
3. **The bundled-brain artifact is present.** Check `${CLAUDE_PLUGIN_ROOT}/brain/server.mjs` is readable. Phase 3 deletes this file from the source tree. If it is present in the user's `${CLAUDE_PLUGIN_ROOT}`, they are on the upgrade boundary — exactly when the wizard should run. If absent, exit Step 0f silently (the user has already upgraded past Phase 3 OR has a stale install with a present config, in which case `/brain-setup` running later in this skill handles them).

If any of the three signals is false, exit Step 0f silently and proceed to Step 1 (Gather Project Information). **Do not announce that you ran the detection.**

If all three signals are true, proceed to S1.

#### S1 — Inform & Consent

Tell the user exactly what is about to happen, present the multi-project shared-DB warning, and offer the migrate vs. start-fresh fork. Wait for explicit consent before proceeding.

Print:

```
A bundled brain installation was detected.

The Atelier Brain has moved to a standalone plugin called `mybrain` (ADR-0055).
This pipeline plugin no longer ships a brain server. To keep your captured
thoughts, decisions, patterns, and lessons working, the brain plugin needs
to migrate.

Your existing brain data will NOT be lost. The database and all its contents
are preserved. Only the brain server process is changing.

If this Postgres database is shared with other atelier-pipeline projects,
the schema migration will affect all of them. Existing data is preserved
(additive migration — new columns added, nothing dropped or renamed).

Two paths are available:

  1. MIGRATE  -- Preserve your existing brain database and re-attach it to
                 mybrain. The wizard takes a backup, stops the old bundled
                 brain, walks you through installing mybrain, and verifies
                 the additive schema migration on first connect. Same DB,
                 same data, same config keys, different MCP server.

  2. FRESH    -- Start over. The wizard drops the existing schema (after a
                 backup), installs mybrain, and lets it create a brand-new
                 brain database against the same Postgres instance.

  3. CANCEL   -- Take no action. The wizard exits without changes. You can
                 re-run /pipeline-setup anytime to revisit.

Which path would you like? (migrate / fresh / cancel)
```

If the user says **cancel** (or anything other than `migrate`/`fresh`): print "Wizard cancelled. Re-run `/pipeline-setup` to revisit." Exit Step 0f. Proceed to Step 1.

If the user says **migrate**: enter the migrate track (S2 → S3 → S4 → S5 → S6).

If the user says **fresh**: enter the fresh track (S2-fresh → S3-fresh → S4-fresh → S5-fresh → S6-fresh).

In both cases, before proceeding to S2 / S2-fresh, capture the timestamp `migration_ts` for the backup filename (`date +%Y%m%dT%H%M%S`) and announce: "Starting migration. Current state: S1 → S2."

#### S2 — Backup (migrate path)

Tell the user what will happen before doing it: "I will take a `pg_dump` backup of your existing brain database to `~/.atelier-brain-backup-{migration_ts}.sql`. This is your insurance policy — if anything goes wrong in a later step, you can restore from this file."

1. **Check `pg_dump` availability.** Run `command -v pg_dump`. If on PATH, proceed to step 2. If not on PATH:
   - Print the manual command the user can run themselves:
     ```
     pg_dump <expanded_database_url> > ~/.atelier-brain-backup-{migration_ts}.sql
     ```
   - Ask: "I cannot find `pg_dump` on PATH (common when your DB is remote and you have no local Postgres tooling). Do you have your own backup, or have you run the command above? Type `yes` to confirm and proceed without me taking the backup, or type `cancel` to exit the wizard."
   - If the user types anything other than exactly `yes`: HALT. Print "S2 HALT: backup acknowledgement not given. Wizard cancelled with no changes." Exit Step 0f. **Do not proceed.**
   - If the user types `yes`: record `backup_path = "(user-managed)"` and proceed to S3.

2. **Take the backup.** Expand `${ENV_VAR}` placeholders in `database_url` against the current environment, then run:
   ```bash
   pg_dump "<expanded_database_url>" > ~/.atelier-brain-backup-{migration_ts}.sql
   ```
   Capture exit code. If non-zero: HALT. Print:
   ```
   S2 HALT — pg_dump failed.

   Current state: old brain still installed, no changes have been made.
   Backup attempt path: ~/.atelier-brain-backup-{migration_ts}.sql
   pg_dump exit code: <code>
   pg_dump stderr: <last 20 lines>

   To resume the wizard later, fix the backup issue and re-run /pipeline-setup.
   To abandon the migration, take no action — your install is unchanged.
   ```
   Exit Step 0f. **Do not proceed.**

3. **Confirm the backup.** Print: "Backup saved to `~/.atelier-brain-backup-{migration_ts}.sql`. To restore later: `psql <expanded_database_url> < ~/.atelier-brain-backup-{migration_ts}.sql`." Record `backup_path`. Proceed to S3.

#### S2-fresh — Backup (fresh path)

Same procedure as S2, with one difference in framing: emphasize that this backup is what lets the user undo the fresh-start if they change their mind. Print before taking the dump: "Even though you chose `fresh`, I'm taking a backup first. If you change your mind after the schema is dropped, you can restore from this file."

All other behavior (PATH check, halt on failure, halt on missing acknowledgement) is identical to S2. Proceed to S3-fresh on success.

#### S3 — Stop & Remove Old Brain (migrate path)

Tell the user what is about to happen: "I am about to stop the old bundled brain. I will NOT drop tables, I will NOT remove `.claude/brain-config.json`, and I will NOT remove the `ATELIER_BRAIN_DB_PASSWORD` environment variable. Your existing brain data will NOT be lost. The database and all its contents are preserved. Only the brain server process is changing."

1. **Detect the database strategy** from `database_url` (already classified at S0). Behavior diverges per strategy:

   - **Docker:** Run `docker compose -f ${CLAUDE_PLUGIN_ROOT}/brain/docker-compose.yml ps` to check container status. If the `brain-db` container is running, run `docker compose -f ${CLAUDE_PLUGIN_ROOT}/brain/docker-compose.yml down`. Capture the exit code. **Do NOT pass `-v` — the volume must survive so the data is preserved across the migration.** If `down` fails: HALT. Print:
     ```
     S3 HALT — docker compose down failed.

     Current state: backup saved at <backup_path>; old brain container may still
     be running. To recover: stop the container manually with
     `docker compose -f ${CLAUDE_PLUGIN_ROOT}/brain/docker-compose.yml down`
     and re-run /pipeline-setup. Backup is still valid.
     ```
     Exit Step 0f.

   - **Local PostgreSQL / Remote PostgreSQL:** No container to stop. The bundled brain runs as an MCP server process spawned by Claude Code; once Phase 3 deletes `brain/`, that process can no longer be spawned. Print: "Your brain runs as a local/remote PostgreSQL connection — there's no separate container or daemon to stop. The bundled brain MCP server stops automatically when the plugin upgrade removes `brain/server.mjs`." Proceed.

2. **Do NOT delete `.claude/brain-config.json`.** Mybrain accepts identical config keys (`database_url`, `scope`, `brain_name`, `openrouter_api_key`, and the ADR-0054 multi-provider fields under identical names). The config is a hand-off, not a translation. Leave the file in place.

3. **Do NOT touch `permissions.allow` directly.** Step 0e earlier in this skill already strips the stale `mcp__plugin_atelier-pipeline_atelier-brain__` prefix entries on every run; mybrain's `brain-setup` re-adds the new-prefixed entries when the user runs it post-install (S4 below).

4. Confirm: "Old brain stopped. Backup at `<backup_path>`. To roll back at this point: restart the bundled brain via `docker compose -f ${CLAUDE_PLUGIN_ROOT}/brain/docker-compose.yml up -d` (Docker only — local/remote setups never had a separate process to restart)."

Proceed to S4.

#### S3-fresh — Drop Schema (fresh path)

Tell the user what will happen: "I am about to DROP the existing brain schema. All thoughts, decisions, patterns, lessons, and relations stored in this database will be permanently deleted. The Postgres database itself remains; only the schema contents go. Your backup at `<backup_path>` is your only recovery path if you change your mind."

1. **Final confirmation.** Ask: "Type exactly `DROP` (uppercase, no quotes) to proceed. Anything else cancels the fresh-start path." If the user types anything other than exactly `DROP`: HALT. Print "S3-fresh HALT: drop confirmation not given. Wizard cancelled with no changes." Exit Step 0f.

2. **Drop the schema.** Expand `${ENV_VAR}` placeholders in `database_url`, then run:
   ```bash
   psql "<expanded_database_url>" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
   ```
   Capture exit code. If non-zero: HALT. Print:
   ```
   S3-fresh HALT — schema drop failed.

   Current state: backup saved at <backup_path>; schema may be in partial state.
   psql exit code: <code>
   psql stderr: <last 20 lines>

   To recover: connect with psql and inspect the schema state, then drop manually:
     psql <expanded_database_url> -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
   To abandon the fresh-start: restore from backup with
     psql <expanded_database_url> < <backup_path>
   ```
   Exit Step 0f.

3. **Stop the old bundled brain** using the same per-strategy logic as S3 step 1 (Docker `compose down`, local/remote no-op). HALT semantics identical to S3.

4. Confirm: "Schema dropped. Old brain stopped. Backup at `<backup_path>`."

Proceed to S4-fresh.

#### S4 — Install mybrain (migrate path)

Tell the user: "I cannot install plugins on your behalf — that requires Claude Code's plugin manager. I will print the install command, and you run it in another shell, then come back here and confirm."

1. Print the install command:
   ```
   Run this in another terminal (or in this one after I finish):

     claude plugin install <mybrain-source-url>

   See the mybrain plugin's README for the exact source URL. The plugin
   will register itself as an MCP server with tool prefix
   `mcp__plugin_mybrain__` (or similar — the suffix-match in the pipeline
   gate hooks accepts any prefix).

   Once the install completes and Claude Code reloads, type `installed`
   to continue, or `cancel` to abort the wizard.
   ```

2. Wait for user input. If the user types anything other than `installed`: HALT. Print "S4 HALT: mybrain install not confirmed. Backup at `<backup_path>`. Wizard exited; re-run `/pipeline-setup` after installing mybrain to resume from this point — the wizard's idempotency check at S0 will detect that mybrain is now registered and skip the rest of Step 0f silently."

3. **Probe ToolSearch to verify mybrain is registered.** Run:
   ```
   ToolSearch query: select:mcp__*__atelier_stats,mcp__*mybrain*
   ```
   If no mybrain-prefixed tool resolves: HALT. Print:
   ```
   S4 HALT — mybrain ToolSearch probe failed.

   Current state: old brain stopped, mybrain not yet detected by Claude Code.
   Backup at <backup_path>.

   This usually means Claude Code has not reloaded the plugin registry. Try:
     1. Reload Claude Code (Cmd+R / restart the session).
     2. Verify the plugin is installed: `claude plugin list | grep mybrain`.
     3. Re-run /pipeline-setup. The wizard's S0 detection will skip Step 0f
        once mybrain is registered.

   To roll back to the bundled brain: uninstall mybrain (`claude plugin uninstall mybrain`),
   reinstall the previous version of atelier-pipeline that still bundles brain/,
   and run `psql <expanded_database_url> < <backup_path>` if any schema changes
   were applied.
   ```
   Exit Step 0f.

4. Confirm: "mybrain is registered. Proceeding to schema verification."

Proceed to S5.

#### S4-fresh — Install mybrain (fresh path)

Identical to S4. The mybrain install command and ToolSearch probe are the same; only the database state differs (empty schema after S3-fresh vs. preserved data after S3). Proceed to S5-fresh on success.

#### S5 — Verify & Migrate Schema (migrate path) — HIGHEST RISK STATE

Tell the user: "Mybrain is now connecting to your existing brain database. On first connect, mybrain runs `runMigrations()` which applies the additive v1→merged migration. Existing data is preserved (new columns are added; nothing is dropped or renamed). I will probe `/health` and run `atelier_stats` to verify the migration succeeded."

This is the **highest-risk state** because: old brain is stopped, mybrain is installed, the database has been touched by `runMigrations()`, and a failure here leaves the user with a half-migrated DB. The HALT message MUST include the exact recovery command — that contract is the load-bearing piece.

1. **Probe mybrain `/health` endpoint.** Mybrain exposes `GET /health` returning `{"status":"ok"}` (per ADR-0055 §Decision). Use the appropriate transport for the user's platform — typically `curl http://localhost:<mybrain-port>/health` or invoke the mybrain `atelier_stats` MCP tool directly.

2. **Run `atelier_stats`** via the now-registered mybrain MCP tool. If it returns a non-empty result with `brain_enabled: true` (or the equivalent ready signal mybrain emits), the migration succeeded.

3. **On success:** Print "Schema migrated. mybrain reports `<N>` tools available, `<scope>` scope active. Proceeding to S6 (cleanup)." Proceed to S5 → S6.

4. **On failure (health probe fails OR atelier_stats fails OR runMigrations error in mybrain logs):** HALT. Print this exact message — the rollback contract requires it:

   ```
   S5 HALT — schema migration failed at the highest-risk state.

   This is the state where:
     - The old bundled brain is stopped.
     - mybrain is installed and registered.
     - Your database is in a partial migration state (runMigrations may have
       applied some columns / tables but not others).

   To recover, run the exact restore command:

     psql <expanded_database_url> < <backup_path>

   This restores your database to the pre-migration state. Then:
     1. Pin mybrain to a known-good version (see mybrain release notes).
     2. Re-run /pipeline-setup. The wizard's S0 detection will not re-trigger
        on the same database (mybrain is registered) — you will need to
        manually clear and re-attempt the migration with mybrain support.

   Backup retained at: <backup_path>
   Database URL: <expanded_database_url>
   Migration ts: <migration_ts>
   ```

   Exit Step 0f.

#### S5-fresh — Verify (fresh path)

Identical to S5 but the database is empty so `runMigrations()` is a fresh apply of the merged schema, not an additive migration on existing data. The probe and HALT semantics are the same. On failure HALT message: same structure as S5, but the recovery command is `psql <expanded_database_url> -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"` followed by re-running `/brain-setup` from the new mybrain plugin. Proceed to S6-fresh on success.

#### S6 — Clear Sentinels & Confirm

1. **Remove sentinel files.** If `docs/pipeline/.brain-not-installed` exists, delete it. If `docs/pipeline/.brain-unavailable` exists, delete it. These were touched by previous sessions when the bundled brain was unreachable; mybrain is now live, so they are stale.

2. **Run a final round-trip.** Call `agent_capture` with a minimal probe payload (`thought_type: 'lesson'`, content: "Brain migration to mybrain completed via Step 0f wizard."), then `agent_search` for the captured content. If both succeed, the migration is verified end-to-end.

3. **On success — print the success summary:**
   ```
   Brain migration complete.

   What changed:
     - Bundled brain server stopped and removed (Phase 3 of ADR-0055).
     - mybrain plugin registered and serving the brain MCP tools.
     - Schema migrated additively (your existing data is preserved).
     - Sentinel files cleared.

   Backup retained at: <backup_path>
   You own retention. Delete it manually when you are confident the migration
   stuck (recommended: keep it for at least a few full pipeline cycles).

   To re-run brain-setup against the new mybrain plugin (e.g., to refresh
   permissions.allow entries with mybrain's tool prefix), run /brain-setup
   from the mybrain plugin.
   ```

4. **On round-trip failure:** Print a soft warning (do NOT halt — mybrain is non-blocking per ADR-0053 / ADR-0055):
   ```
   S6 SOFT WARNING — final round-trip probe did not return cleanly. Brain
   migration is structurally complete, but agent_capture / agent_search did
   not round-trip on this attempt. Your pipeline still works because the
   brain is non-blocking. Re-run /brain-setup against mybrain to diagnose.

   Backup retained at: <backup_path>
   ```
   Exit Step 0f normally.

#### S6-fresh — Confirm (fresh path)

Same as S6 but the success message reads "Brain reset complete" rather than "migration complete," and notes that the previous data has been deleted (the backup is the only copy of it).

#### Step 0f Idempotency

After successful migration, the next `/pipeline-setup` invocation hits S0 and exits silently (mybrain is registered → signal 1 fails). This is the load-bearing idempotency contract. If a partially-migrated install re-triggers the wizard (e.g., S2 succeeded but S5 failed), the user must follow the HALT recovery command first; the wizard does not auto-resume from arbitrary failure states. Once the user restores the backup or completes recovery manually, the next run hits S0 with old-brain-still-bundled-but-mybrain-registered, signal 1 fails, and Step 0f exits silently.

#### Step 0f Config Key Migration

There is no config key translation. Mybrain accepts every key the atelier-brain `brain-config.json` writes — `database_url`, `scope`, `brain_name`, `openrouter_api_key`, `embedding_provider` / `embedding_model` / `embedding_api_key` / `embedding_base_url`, `chat_provider` / `chat_model` / `chat_api_key` / `chat_base_url` — under the same names. The wizard does NOT rename any keys, does NOT translate any values, and does NOT rewrite `.claude/brain-config.json`. The migration is a hand-off, not a translation.

The `permissions.allow` rewrite is handled by Step 0e earlier in this skill (which strips the stale `mcp__plugin_atelier-pipeline_atelier-brain__` prefix on every run); mybrain's own `brain-setup` skill re-adds the new-prefixed entries when the user runs it.

### Step 1: Gather Project Information

Before installing, ask the user about their project. Ask these questions conversationally, one at a time -- do not dump a list.

**Required information:**

0. **Project name** -- A short identifier for this project (e.g., "syntetiq", "atelier-pipeline", "my-app"). Used in telemetry scope for cross-project tracking. Ask: "What should I call this project in telemetry reports?"
1. **Tech stack** -- Language, framework, runtime (e.g., "React 19 with Vite, Express.js backend, PostgreSQL")
2. **Test framework** -- What testing library/runner (e.g., "Vitest", "Jest", "pytest", "cargo test")
3. **Test commands** -- The exact commands for:
   - **Lint command** -- fast lint/typecheck checks with no DB or external dependencies, used by agents during their workflow (e.g., `npm run lint && tsc --noEmit`, `black --check . && ruff check . && mypy .`).
   - **Full test suite** -- the complete test suite including DB-dependent and integration tests, used by Poirot for QA verification (e.g., `npm test`, `pytest --cov`). Runs once per work unit.
   - Running a single test file (e.g., `npx vitest run path/to/file`)
4. **Source structure** -- Where features, components, services, and routes live. Specifically ask for:
   - **Project source directory** -- Root directory for source code (e.g., `src/`, `lib/`, `app/`)
   - **Feature directory pattern** -- Where feature directories live (e.g., `src/features/`, `app/domains/`)
   - **Overall layout** -- How components and services are organized (e.g., "src/features/<feature>/ for frontend, services/api/ for backend")
5. **Database/store pattern** -- How database access is structured (e.g., "Factory functions with closures over DB client", "Prisma ORM", "raw SQL with pg")
6. **Build/deploy commands** -- How the project builds and ships (e.g., `npm run build`, Docker, Podman Compose)
7. **Coverage thresholds** -- If they have existing targets (statement, branch, function, line percentages)

If the user does not have answers for optional items (coverage), use sensible defaults.

### Step 1a: Design System Path (Optional)

Some projects keep their design system (tokens, components, icons) in a
directory outside the project root -- a shared monorepo package, a sibling
directory, or an external path. By default, agents look for a
`design-system/` directory at the project root. If yours lives elsewhere,
configure the path now.

Ask conversationally (not as a list):

> Does your project have a design system directory, and is it at the default
> `design-system/` path at the project root?
>
> - **Yes, default path** (or "I don't have a design system"): press Enter.
> - **Yes, external path:** provide the absolute or project-relative path.

**If user provides a path:**

1. **Validate existence.** Check that the path exists. If not found, print
   `Directory [path] not found -- skipping design-system path configuration.`
   and continue without setting the path.
2. **Validate tokens.md.** Check that `tokens.md` exists inside the directory.
   If missing, print `No tokens.md found at [path]. Skipping -- a valid design
   system must include tokens.md.` and continue without setting the path.
3. **Set config.** Resolve to absolute path, and store in
   `.claude/pipeline-config.json` as `design_system_path`.
4. **List discovered files.** Print: `Design system path set to [path]. Found:
   [list of .md files]. [icons/ directory present | No icons/ directory]`.

**If user does not provide a path (default or absent):**

Leave `design_system_path` as `null` in `pipeline-config.json` (the template
default). Agents will fall back to convention-based detection (`design-system/`
at project root). Print nothing -- this is the common case.

**To change the path later:** re-run `/pipeline-setup` (this step is idempotent
and will re-prompt).

### Step 1b: Git Repository Detection

Before asking about branching strategy, determine git availability.

1. Run `git rev-parse --git-dir 2>/dev/null`. If this succeeds, set `git_available: true` and proceed to Step 1c (branching strategy selection).

2. If no git repo detected, inform the user:

> This project does not have a git repository.
>
> **What still works without git:**
> Eva (orchestrator), Robert (product), Sable (UX), Sarah (architect), Colby (engineer), Poirot, Sentinel (security), Agatha (docs), Brain (memory), enforcement hooks
>
> **What is unavailable without git:**
> Poirot (blind review -- needs git diff), Ellis (commit manager -- needs git), CI Watch (needs git + platform CLI), branch lifecycle management

> Would you like to create a git repository now?

3. **If user says yes:** Run `git init`, create a sensible `.gitignore` (node_modules/, .env, dist/, etc. based on detected tech stack), run `git add .gitignore && git commit -m "Initial commit"`. Set `git_available: true`, proceed to Step 1c (branching strategy selection).

4. **If user says no:** Set `git_available: false` in pipeline-config.json. Skip Step 1c entirely. Skip platform CLI detection. Skip CI Watch offer (Step 6c). Log: "Git unavailable -- skipping branching strategy, platform CLI, and CI Watch configuration." Proceed to Step 1d.

5. **If `git init` fails** (e.g., permission error): Set `git_available: false` and proceed as in step 4. Inform: "Git init failed -- proceeding without git. You can run `git init` manually later and re-run `/pipeline-setup`."

### Step 1c: Branching Strategy Selection

**Pre-checks (before asking):**

1. Check `git remote get-url origin` -- if no remote, auto-select trunk-based with message: "No remote detected -- defaulting to trunk-based. Run setup again after adding a remote to configure MR-based flows." Skip to next step.

**If git + remote exist, ask the user (one question, not a list dump):**

> Which branching strategy should the pipeline use?
> - **Trunk-Based Development** (Recommended for solo/small teams) -- Commit directly to main. Simplest setup.
> - **GitHub Flow** -- Feature branches + merge requests. Main is always deployable.
> - **GitLab Flow** -- GitHub Flow + environment branches (staging, production). For staged deployments.
> - **GitFlow** -- Formal release cycle with develop + main. For versioned software with scheduled releases.

**Follow-up per strategy:**

- **Trunk-based:** No follow-up needed.
- **GitHub Flow / GitLab Flow / GitFlow:** Detect platform from remote URL (github -> `gh`, gitlab -> `glab`). If unrecognizable, ask user. Then check CLI availability (`which gh` or `which glab`). If missing, detect package manager (try `which brew`, `which apt-get`, `which dnf` in order). If package manager found, offer: "[Strategy] requires `[cli]` CLI, which isn't installed. Install with `[pm] install [cli]`?" Options: "Install it for me" / "I'll install it later". If no package manager found: "Please install `[cli]` CLI before running the pipeline. See [install URL]."
- **GitLab Flow additional:** Ask "What are your environment branch names?" Default: staging, production.
- **GitFlow:** Platform detection only, no additional questions (conventions are standardized). Integration branch is `develop`.

**Store selection:** Write `.claude/pipeline-config.json` with the appropriate values from `source/shared/pipeline/pipeline-config.json` as the template, filled with the user's selections. The template includes `design_system_path: null` (convention-based auto-detection). Use `/load-design` after setup to configure an external design system path if needed.

### Step 1d: Model Provider Selection

Ask the user one question:

> Which model provider does your Claude Code environment use?
> - **anthropic** (default) -- Standard Anthropic API (api.anthropic.com). No extra setup beyond `ANTHROPIC_API_KEY`.
> - **bedrock** -- AWS Bedrock. Requires `ANTHROPIC_AWS_REGION` plus one of: `AWS_PROFILE` or the `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` key pair. You must also enable Claude model access in the AWS Bedrock console for your region before running the pipeline.
> - **vertex** -- Google Vertex AI. Requires `ANTHROPIC_VERTEX_PROJECT_ID`, `CLOUD_ML_REGION`, and service account authentication (either `GOOGLE_APPLICATION_CREDENTIALS` pointing to a service account JSON key, or `gcloud auth application-default login`).

**Default:** If the user presses Enter without selecting, default to `anthropic`. This keeps existing deployments unaffected.

**Credential note (read aloud or display after selection):**

> Credentials stay in your Claude Code environment — the pipeline only needs to know which ID shape to emit. Do not put API keys or cloud credentials in pipeline-config.json.

**Provider-specific follow-up:**

- **anthropic:** No further questions. Proceed.
- **bedrock:** Confirm: "Make sure `ANTHROPIC_AWS_REGION` is set in your Claude Code environment, and that you have either `AWS_PROFILE` or the `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` pair configured. Also verify that Claude model access is enabled in the AWS Bedrock console for your region." No input required — informational only.
- **vertex:** Confirm: "Make sure `ANTHROPIC_VERTEX_PROJECT_ID` and `CLOUD_ML_REGION` are set in your Claude Code environment, and that service account auth is configured (via `GOOGLE_APPLICATION_CREDENTIALS` or `gcloud auth application-default login`)." No input required — informational only.

**Write model_provider:** The template ships with `"model_provider": "anthropic"` — no file change is needed when the user selects the default. For `bedrock` or `vertex`, update `.claude/pipeline-config.json` to set `model_provider` to the selected value.

### Step 2: Read Templates

Read the template files from the plugin's templates directory. These serve as the base for each installed file. Source files are split into three directories: `source/shared/` (platform-agnostic content), `source/claude/` (Claude Code overlays), and `source/cursor/` (Cursor overlays).

**Platform detection:** If the environment variable `CURSOR_PROJECT_DIR` is set, use Cursor overlays from `source/cursor/`. Otherwise, use Claude Code overlays from `source/claude/`. `CURSOR_PROJECT_DIR` takes precedence over `CLAUDE_PROJECT_DIR` -- when both are set, the Cursor overlay is used.

**Overlay assembly procedure (agents):** Agent persona files are assembled at install time by combining a platform-specific frontmatter overlay with shared content:

1. Read `source/{claude|cursor}/agents/{name}.frontmatter.yml` (YAML frontmatter only, no `---` delimiters)
2. Read `source/shared/agents/{name}.md` (content body, no frontmatter)
3. Concatenate: `---\n` + frontmatter content + `---\n` + body content
4. Write the assembled file to the target project (e.g., `.claude/agents/{name}.md`)

**Overlay assembly procedure (commands, rules, variants):** Same pattern -- platform-specific frontmatter overlay + shared content body, concatenated with `---` delimiters.

```
plugins/atelier-pipeline/source/
  shared/                              # Platform-agnostic content (no YAML frontmatter)
    agents/
      sarah.md                           # Architect subagent content body
      colby.md                         # Engineer subagent content body
      robert.md                        # Product reviewer subagent content body
      sable.md                         # UX reviewer subagent content body
      investigator.md                  # Poirot (blind investigator) content body
      distillator.md                   # Compression engine content body
      ellis.md                         # Commit manager content body
      agatha.md                        # Documentation subagent content body
    commands/
      pm.md                            # /pm -- Robert (product)
      ux.md                            # /ux -- Sable (UX design)
      architect.md                     # /architect -- Sarah (architecture)
      pipeline.md                      # /pipeline -- Eva (orchestration)
      devops.md                        # /devops -- Eva (infrastructure)
      docs.md                          # /docs -- Agatha (documentation)
    references/
      dor-dod.md                       # Definition of Ready / Definition of Done framework
      invocation-templates.md          # Subagent invocation examples
      pipeline-operations.md           # Operational procedures (model selection, QA flow, feedback loops)
      agent-preamble.md               # Shared agent required actions (DoR/DoD, retro, brain)
      branch-mr-mode.md               # Colby branch/MR procedures for MR-based strategies
      step-sizing.md                  # ADR step sizing gate (S1-S5) and split heuristics
    pipeline/
      pipeline-state.md               # Session recovery state template
      context-brief.md                # Context preservation template
      error-patterns.md               # Error pattern log template
      investigation-ledger.md         # Debug hypothesis tracking template
      pipeline-config.json            # Branching strategy configuration
    rules/
      default-persona.md              # Eva orchestrator persona
      agent-system.md                 # Full orchestration rules, routing, gates
    variants/
      branch-lifecycle-trunk-based.md  # Trunk-based branch lifecycle
      branch-lifecycle-github-flow.md  # GitHub Flow branch lifecycle
      branch-lifecycle-gitlab-flow.md  # GitLab Flow branch lifecycle
      branch-lifecycle-gitflow.md      # GitFlow branch lifecycle
  claude/                              # Claude Code overlays
    agents/*.frontmatter.yml           # Claude Code frontmatter for each agent
    hooks/                             # Enforcement hook scripts
    commands/*.frontmatter.yml         # Command frontmatter overlays
    rules/*.frontmatter.yml            # Rule frontmatter overlays
    variants/*.frontmatter.yml         # Variant frontmatter overlays
  cursor/                              # Cursor overlays
    agents/*.frontmatter.yml           # Cursor frontmatter for each agent (no hooks field)
    hooks/hooks.json                   # Cursor hook configuration
    commands/*.frontmatter.yml         # Command frontmatter overlays
    rules/*.frontmatter.yml            # Rule frontmatter overlays
    variants/*.frontmatter.yml         # Variant frontmatter overlays
```

> **Enforcement hook bypass:** Before the first write operation below, create
> the setup-mode sentinel file to disable enforcement hooks for this session.
> This allows /pipeline-setup to write to `.claude/` paths even when
> enforcement hooks are already installed (re-install or update scenario).
>
> 1. Ensure `docs/pipeline/` exists: `mkdir -p docs/pipeline`
> 2. Create sentinel: write an empty file to `docs/pipeline/.setup-mode`
>
> After all files are installed (end of Step 6d), remove the sentinel:
> delete `docs/pipeline/.setup-mode`.
>
> The sentinel file is also checked into `.gitignore` patterns in the
> pipeline state directory template to avoid accidental commits.

### Step 3: Install Files

Copy each template to its destination in the user's project, customizing placeholders with the project-specific values gathered in Step 1.

**Installation manifest:**

Files are assembled from `source/shared/` (content) + `source/claude/` (overlays) for Claude Code, or `source/shared/` + `source/cursor/` for Cursor. Agent files use overlay assembly (frontmatter + content concatenation). Other files copy from `source/shared/` directly.

| Template Source | Destination | Purpose |
|----------------|-------------|---------|
| `source/shared/rules/default-persona.md` assembled with `source/claude/rules/` overlay | `.claude/rules/default-persona.md` | Eva persona -- always loaded by Claude Code |
| `source/shared/rules/agent-system.md` assembled with overlay | `.claude/rules/agent-system.md` | Orchestration rules, routing table, quality gates |
| `source/shared/rules/pipeline-orchestration.md` assembled with overlay | `.claude/rules/pipeline-orchestration.md` | Pipeline operations (path-scoped) |
| `source/shared/rules/pipeline-models.md` assembled with overlay | `.claude/rules/pipeline-models.md` | Model selection (path-scoped) |
| `source/shared/agents/sarah.md` + `source/claude/agents/sarah.frontmatter.yml` | `.claude/agents/sarah.md` | Architect subagent persona (overlay assembly) |
| `source/shared/agents/colby.md` + `source/claude/agents/colby.frontmatter.yml` | `.claude/agents/colby.md` | Engineer subagent persona (overlay assembly) |
| `source/shared/agents/robert.md` + `source/claude/agents/robert.frontmatter.yml` | `.claude/agents/robert.md` | Product reviewer subagent persona (overlay assembly) |
| `source/shared/agents/sable.md` + `source/claude/agents/sable.frontmatter.yml` | `.claude/agents/sable.md` | UX reviewer subagent persona (overlay assembly) |
| `source/shared/agents/investigator.md` + `source/claude/agents/investigator.frontmatter.yml` | `.claude/agents/investigator.md` | Blind investigator subagent persona (overlay assembly) |
| `source/shared/agents/distillator.md` + `source/claude/agents/distillator.frontmatter.yml` | `.claude/agents/distillator.md` | Compression engine subagent persona (overlay assembly) |
| `source/shared/agents/ellis.md` + `source/claude/agents/ellis.frontmatter.yml` | `.claude/agents/ellis.md` | Commit manager subagent persona (overlay assembly) |
| `source/shared/agents/agatha.md` + `source/claude/agents/agatha.frontmatter.yml` | `.claude/agents/agatha.md` | Documentation subagent persona (overlay assembly) |
| `source/shared/agents/robert-spec.md` + `source/claude/agents/robert-spec.frontmatter.yml` | `.claude/agents/robert-spec.md` | Product spec producer subagent persona (overlay assembly) |
| `source/shared/agents/sable-ux.md` + `source/claude/agents/sable-ux.frontmatter.yml` | `.claude/agents/sable-ux.md` | UX design producer subagent persona (overlay assembly) |
| `source/shared/agents/scout.md` + `source/claude/agents/scout.frontmatter.yml` | `.claude/agents/scout.md` | Read-only file/grep/read scout subagent persona (overlay assembly, ADR-0048) |
| `source/shared/agents/synthesis.md` + `source/claude/agents/synthesis.frontmatter.yml` | `.claude/agents/synthesis.md` | Post-scout filter/rank/trim synthesis subagent persona (overlay assembly, ADR-0048) |
| `source/shared/commands/pm.md` assembled with overlay | `.claude/commands/pm.md` | /pm slash command |
| `source/shared/commands/ux.md` assembled with overlay | `.claude/commands/ux.md` | /ux slash command |
| `source/shared/commands/architect.md` assembled with overlay | `.claude/commands/architect.md` | /architect slash command |
| `source/shared/commands/pipeline.md` assembled with overlay | `.claude/commands/pipeline.md` | /pipeline slash command |
| `source/shared/commands/devops.md` assembled with overlay | `.claude/commands/devops.md` | /devops slash command |
| `source/shared/commands/docs.md` assembled with overlay | `.claude/commands/docs.md` | /docs slash command |
| `source/shared/references/dor-dod.md` | `.claude/references/dor-dod.md` | Quality framework |
| `source/shared/references/invocation-templates.md` | `.claude/references/invocation-templates.md` | Subagent invocation examples |
| `source/shared/references/pipeline-operations.md` | `.claude/references/pipeline-operations.md` | Operational procedures (model selection, QA, feedback, batch, worktree, context) |
| `source/shared/references/agent-preamble.md` | `.claude/references/agent-preamble.md` | Shared agent required actions |
| `source/shared/references/branch-mr-mode.md` | `.claude/references/branch-mr-mode.md` | Colby branch/MR procedures |
| `source/shared/references/telemetry-metrics.md` | `.claude/references/telemetry-metrics.md` | Telemetry metric schemas, cost table, alert thresholds (also holds JIT telemetry-capture protocol) |
| `source/shared/references/pipeline-phases.md` | `.claude/references/pipeline-phases.md` | JIT phase sizing, budget gate, investigation discipline, concurrent session detection, state file descriptions |
| `source/shared/references/worktree-isolation.md` | `.claude/references/worktree-isolation.md` | JIT worktree-per-session protocol (ADR-0038) |
| `source/shared/references/step-sizing.md` | `.claude/references/step-sizing.md` | ADR step sizing gate (S1-S5) and split heuristics |
| `source/shared/pipeline/pipeline-state.md` | `docs/pipeline/pipeline-state.md` | Session recovery state |
| `source/shared/pipeline/context-brief.md` | `docs/pipeline/context-brief.md` | Context preservation |
| `source/shared/pipeline/error-patterns.md` | `docs/pipeline/error-patterns.md` | Error pattern tracking |
| `source/shared/pipeline/investigation-ledger.md` | `docs/pipeline/investigation-ledger.md` | Debug hypothesis tracking |
| `source/shared/pipeline/pipeline-config.json` | `.claude/pipeline-config.json` | Branching strategy configuration |
| `source/shared/variants/branch-lifecycle-{strategy}.md` assembled with overlay | `.claude/rules/branch-lifecycle.md` | Branch lifecycle rules (selected variant only) |

**Total: 30 mandatory files across 5 directories (before hooks and config).**

**State file guard:** The 5 pipeline state files in `docs/pipeline/` and `.claude/pipeline-config.json` are live state — they contain active pipeline progress, user decisions, and project configuration. On re-install or update:
- If the destination file already exists, **skip it** — do not overwrite
- If the destination file does not exist, copy the template (fresh install)
- To force a reset, the user must explicitly delete the file first

This guard does NOT apply to rules, agents, commands, references, or hooks — those are always overwritten from source templates on re-sync.

### Step 3a: Install Enforcement Hooks

Copy the hook scripts from the plugin's `source/claude/hooks/` directory to `.claude/hooks/`
in the project. These hooks mechanically enforce agent boundaries — they are not
optional and must be installed for the pipeline to function correctly.

| Template Source | Destination | Purpose |
|----------------|-------------|---------|
| `source/claude/hooks/enforce-eva-paths.sh` | `.claude/hooks/enforce-eva-paths.sh` | Blocks main thread (Eva) Write/Edit outside docs/pipeline/ |
| `source/claude/hooks/enforce-sarah-paths.sh` | `.claude/hooks/enforce-sarah-paths.sh` | Per-agent: Sarah can only write to docs/architecture/ |
| `source/claude/hooks/enforce-colby-paths.sh` | `.claude/hooks/enforce-colby-paths.sh` | Per-agent: Colby blocked from colby_blocked_paths |
| `source/claude/hooks/enforce-agatha-paths.sh` | `.claude/hooks/enforce-agatha-paths.sh` | Per-agent: Agatha can only write to docs/ |
| `source/claude/hooks/enforce-product-paths.sh` | `.claude/hooks/enforce-product-paths.sh` | Per-agent: Robert-spec can only write to docs/product/ |
| `source/claude/hooks/enforce-ux-paths.sh` | `.claude/hooks/enforce-ux-paths.sh` | Per-agent: Sable-ux can only write to docs/ux/ |
| `source/claude/hooks/enforce-ellis-paths.sh` | `.claude/hooks/enforce-ellis-paths.sh` | Per-agent: Ellis can only write to CHANGELOG.md, git config files, and CI/CD paths |
| `source/claude/hooks/enforce-sequencing.sh` | `.claude/hooks/enforce-sequencing.sh` | Blocks out-of-order agent invocations (e.g., Ellis without Poirot verification) |
| `source/claude/hooks/enforce-pipeline-activation.sh` | `.claude/hooks/enforce-pipeline-activation.sh` | Blocks Colby/Ellis invocation when no active pipeline exists |
| `source/claude/hooks/enforce-scout-swarm.sh` | `.claude/hooks/enforce-scout-swarm.sh` | Blocks Sarah/Colby/Poirot invocations missing the required scout evidence block (research-brief, colby-context, debug-evidence, qa-evidence) |
| `source/claude/hooks/enforce-git.sh` | `.claude/hooks/enforce-git.sh` | Blocks git write operations from main thread (must go through Ellis) |
| `source/claude/hooks/session-hydrate.sh` | `.claude/hooks/session-hydrate.sh` | Intentional no-op — superseded by atelier_hydrate MCP tool. Installed for backward-compatibility only; NOT registered in settings.json. |
| `source/claude/hooks/pre-compact.sh` | `.claude/hooks/pre-compact.sh` | Writes compaction marker to pipeline-state.md before context is compacted (PreCompact) |
| `source/claude/hooks/log-agent-start.sh` | `.claude/hooks/log-agent-start.sh` | Logs agent start events to JSONL telemetry file (SubagentStart) |
| `source/claude/hooks/log-agent-stop.sh` | `.claude/hooks/log-agent-stop.sh` | Logs agent stop events to JSONL telemetry file (SubagentStop) |
| `source/claude/hooks/enforce-colby-stop-verify.sh` | `.claude/hooks/enforce-colby-stop-verify.sh` | Runs verify_commands.format + verify_commands.typecheck after Colby stops; exits 2 on typecheck failure to re-engage Colby (SubagentStop, ADR-0050). **Claude Code only -- Cursor does not support SubagentStop** (see `source/cursor/agents/brain-extractor.frontmatter.yml`); Cursor installs intentionally omit this hook. |
| `source/claude/hooks/post-compact-reinject.sh` | `.claude/hooks/post-compact-reinject.sh` | Re-injects pipeline-state.md and context-brief.md after compaction (PostCompact) |
| `source/claude/hooks/log-stop-failure.sh` | `.claude/hooks/log-stop-failure.sh` | Appends error entry to error-patterns.md on agent failure (StopFailure) |
| `source/claude/hooks/prompt-brain-prefetch.sh` | `.claude/hooks/prompt-brain-prefetch.sh` | Brain prefetch prompt injection (Prompt) |
| `source/claude/hooks/prompt-compact-advisory.sh` | `.claude/hooks/prompt-compact-advisory.sh` | Wave-boundary compaction advisory (SubagentStop) |
| `source/shared/agents/brain-extractor.md` | `.claude/agents/brain-extractor.md` | Brain knowledge extractor agent (assembled with frontmatter overlay below) |
| `source/claude/agents/brain-extractor.frontmatter.yml` | (assembled with above into `.claude/agents/brain-extractor.md`) | Claude Code frontmatter for brain-extractor agent |
| `source/cursor/agents/brain-extractor.frontmatter.yml` | `.cursor-plugin/agents/brain-extractor.md` | Cursor frontmatter for brain-extractor agent |
| `source/shared/hooks/session-boot.sh` | `.claude/hooks/session-boot.sh` | Session boot data collector (SessionStart) -- reads pipeline state and config |
| `source/shared/hooks/hook-lib.sh` | `.claude/hooks/hook-lib.sh` | Shared hook utility library — JSON parsers, agent type extraction, deny/allow emitters (sourced by enforcement and telemetry hooks) |
| `source/shared/hooks/pipeline-state-path.sh` | `.claude/hooks/pipeline-state-path.sh` | Per-worktree session state path resolver — session_state_dir() and error_patterns_path() (sourced by session-boot, post-compact-reinject, prompt-compact-advisory) |
| `source/claude/hooks/enforcement-config.json` | `.claude/hooks/enforcement-config.json` | Project-specific paths and agent rules |

#### ADR-0050 verify_commands keys (`enforce-colby-stop-verify.sh`, opt-in)

The Claude Code-only `enforce-colby-stop-verify.sh` hook (SubagentStop) reads
three keys from `.claude/pipeline-config.json` (or `.cursor/pipeline-config.json`,
checked first). All three are opt-in -- absent or empty values turn the
behavior off without warnings.

| Key | Type | Default | Meaning |
|-----|------|---------|---------|
| `verify_commands.format` | string | (missing) | Auto-format command run after every Colby stop. **Empty string = no-op** (skip the format step). **Missing key = silent skip** (same as empty). Format failures are logged to stderr but never block. |
| `verify_commands.typecheck` | string | (missing) | Typecheck command run after format. **Empty string = no-op** (skip the typecheck step). **Missing key = silent skip**. On non-zero exit the hook prints the last ~40 lines of output on stderr and exits 2 to re-engage Colby. |
| `verify_max_attempts` | integer | `3` | Maximum number of consecutive **typecheck failures** in a single session before the hook stops re-engaging Colby and exits 0 with a warning. The counter increments on failure only; a successful typecheck deletes the counter file (full reset). Format failures never touch the counter. |

If both `verify_commands.format` and `verify_commands.typecheck` are missing
or empty, the hook exits 0 immediately -- the project is treated as not
opted in. To opt in to typecheck-only enforcement, set
`verify_commands.typecheck` and leave `verify_commands.format` empty (or
omit it entirely).

Example (`pipeline-config.json` fragment):

```json
{
  "verify_commands": {
    "format": "npm run format",
    "typecheck": "npm run typecheck"
  },
  "verify_max_attempts": 3
}
```

After copying, make the `.sh` files executable: `chmod +x .claude/hooks/*.sh`

**Validate enforcement-config.json** after copying and customizing. Read the installed `.claude/hooks/enforcement-config.json` and check the following required fields:

| Field | Type | Requirement |
|-------|------|-------------|
| `pipeline_state_dir` | string | Non-empty |
| `test_command` | string | Non-empty -- critical: Poirot cannot run tests without this |
| `test_patterns` | array | Non-empty -- at least one pattern required |

Also check `lint_command`: if the field is absent or empty, warn (but do not block) -- Eva's quality gate will fall back to `test_command`.

Print the validation result:
- **All required fields valid:** `Enforcement config validated — all required fields present.`
- **Any required field missing or empty:** `WARNING: enforcement-config.json is missing required fields: [list]. Pipeline enforcement may not work correctly. Re-run /pipeline-setup to fix.`
- **Only lint_command empty/absent:** `NOTE: lint_command is not set — Eva will fall back to test_command for quality checks.`

Do not block installation on validation failure. The warning is informational -- the fix is re-running setup.

**Customize enforcement-config.json** with the project-specific values from Step 1:
- `pipeline_state_dir`: the pipeline state directory (default: `docs/pipeline`)
- `colby_blocked_paths`: array of path prefixes Colby cannot write to (default includes `docs/`, `.github/`, infrastructure paths)
- `test_patterns`: array of patterns matching the project's test files (e.g., `[".test.", ".spec.", "/tests/", "conftest"]`)
- `test_command`: full test suite command from Step 1 -- used by Poirot for QA verification (e.g., `npm test`, `pytest`)

**Register hooks in `.claude/settings.json`** — merge with existing settings if the
file already exists. Add this hooks section:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-eva-paths.sh"}]
      },
      {
        "matcher": "Agent",
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-sequencing.sh"}, {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-pipeline-activation.sh"}, {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-scout-swarm.sh", "if": "tool_input.subagent_type == 'sarah' || tool_input.subagent_type == 'colby' || tool_input.subagent_type == 'scout'"}, {"type": "prompt", "prompt": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/prompt-brain-prefetch.sh", "if": "tool_input.subagent_type == 'sarah' || tool_input.subagent_type == 'colby' || tool_input.subagent_type == 'poirot'"}]
      },
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-git.sh", "if": "tool_input.command.includes('git ')"}]
      }
    ],
    "SubagentStart": [
      {
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/log-agent-start.sh"}]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-boot.sh"}
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/log-agent-stop.sh"
          },
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-colby-stop-verify.sh"
          },
          {
            "type": "prompt",
            "prompt": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/prompt-compact-advisory.sh",
            "if": "agent_type == 'ellis'"
          },
          {
            "type": "agent",
            "agent": "brain-extractor",
            "prompt": "Extract decisions, patterns, and lessons from the completed agent's output and capture them to the brain via agent_capture.",
            "if": "agent_type == 'sarah' || agent_type == 'colby' || agent_type == 'agatha' || agent_type == 'robert' || agent_type == 'robert-spec' || agent_type == 'sable' || agent_type == 'sable-ux' || agent_type == 'ellis'"
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pre-compact.sh"}]
      }
    ],
    "PostCompact": [
      {
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/post-compact-reinject.sh"}]
      }
    ],
    "StopFailure": [
      {
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/log-stop-failure.sh"}]
      }
    ]
  }
}
```

**Important:** These hooks require `jq` to be installed. Check with `command -v jq`.
If `jq` is not available, tell the user: "Install jq for pipeline enforcement hooks:
`brew install jq` (macOS) or `apt install jq` (Linux)."

**Total with hooks: 38 mandatory files across 7 directories.**

#### Custom Agent Discovery

The pipeline supports custom agents beyond the core 9. To add a custom agent:

- **Drop a file:** Place any `.md` file into `.claude/agents/` with YAML
  frontmatter (`name`, `description`) and Eva will discover it automatically
  at session start.
- **Paste markdown:** Paste a raw agent definition into the chat and Eva will
  offer to convert it to the pipeline's XML format and write it as a proper
  agent file.
- **Read-only by default:** Discovered agents cannot use Write, Edit, or
  MultiEdit tools. To grant write access, add a per-agent frontmatter hook
  (enforce-{name}-paths.sh) to the agent's frontmatter overlay.

See the "Agent Discovery" section in `agent-system.md` for full details.

### Step 3b: Write Version Marker

After copying all template files, write the current plugin version to `.claude/.atelier-version`:

```bash
# Read version from plugin.json and write to project
grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json" | head -1 | grep -o '"[^"]*"$' | tr -d '"' > .claude/.atelier-version
```

This file is used by the SessionStart hook to detect when the plugin has been updated and the project's pipeline files may be outdated. The hook compares this version against the plugin's current version and notifies the user if an update is available.

**Important:** Always write this file, even on reinstalls. It must reflect the version of the templates that were actually installed.

### Step 3c: Cursor Plugin Rules Sync (.mdc wrappers for reference docs)

When running inside Cursor (detected via `CURSOR_PROJECT_DIR` env var), create `.mdc` wrappers
for reference documents so Cursor can discover and load them. Each wrapper adds YAML frontmatter
to the source content. All reference rules use `alwaysApply: false` -- they are loaded on demand
by agents, not injected into every conversation.

**File structure (each reference .mdc wrapper):**

```markdown
---
description: [short description of the document]
alwaysApply: false
---

[Full content from source/shared/references/<file>.md]
```

**Reference docs to sync (alwaysApply: false):**

| Source | Destination | Description |
|--------|-------------|-------------|
| `source/shared/references/dor-dod.md` | `.cursor-plugin/rules/dor-dod.mdc` | Definition of Ready / Definition of Done framework |
| `source/shared/references/invocation-templates.md` | `.cursor-plugin/rules/invocation-templates.mdc` | Invocation templates -- standardized XML tag patterns for subagent invocation |
| `source/shared/references/pipeline-operations.md` | `.cursor-plugin/rules/pipeline-operations.mdc` | Pipeline operations -- continuous QA, feedback loops, batch mode, and worktree rules |
| `source/shared/references/agent-preamble.md` | `.cursor-plugin/rules/agent-preamble.mdc` | Agent preamble -- shared actions and protocols for all pipeline agents |
| `source/shared/references/branch-mr-mode.md` | `.cursor-plugin/rules/branch-mr-mode.mdc` | Branch and MR mode -- Colby branch creation and MR procedures for MR-based strategies |
| `source/shared/references/telemetry-metrics.md` | `.cursor-plugin/rules/telemetry-metrics.mdc` | Telemetry metrics -- metric schemas, cost table, alert thresholds, JIT telemetry-capture protocol |
| `source/shared/references/pipeline-phases.md` | `.cursor-plugin/rules/pipeline-phases.mdc` | JIT phase sizing, budget gate, investigation discipline, concurrent session detection, state file descriptions |
| `source/shared/references/worktree-isolation.md` | `.cursor-plugin/rules/worktree-isolation.mdc` | JIT worktree-per-session protocol (ADR-0038) |
| `source/shared/references/xml-prompt-schema.md` | `.cursor-plugin/rules/xml-prompt-schema.mdc` | XML prompt schema -- tag vocabulary for agent persona files |
| `source/shared/references/cloud-architecture.md` | `.cursor-plugin/rules/cloud-architecture.mdc` | Cloud architecture -- reference for cloud-native deployment patterns |
| `source/shared/references/step-sizing.md` | `.cursor-plugin/rules/step-sizing.mdc` | ADR step sizing gate (S1-S5) and split heuristics |
| `source/shared/references/routing-detail.md` | `.cursor-plugin/rules/routing-detail.mdc` | Auto-routing intent detection matrix -- loaded JIT when Eva encounters edge-case routing decisions |

**Skip when:** Running in Claude Code (no `CURSOR_PROJECT_DIR` env var). Claude Code reads `.claude/references/*.md` directly without `.mdc` wrappers.

### Step 4: Customize Placeholders

The following placeholders in template files must be replaced with project-specific values:

| Placeholder | Replaced With | Example |
|-------------|---------------|---------|
| `{project_name}` | Project name for telemetry | `syntetiq`, `my-app` |
| `{{TECH_STACK}}` | Project tech stack description | "React 19 (Vite), Express.js, PostgreSQL" |
| `{{LINT_COMMAND}}` | Lint command | `npm run lint` |
| `{{TYPECHECK_COMMAND}}` | Type check command | `npm run typecheck` |
| `{{TEST_COMMAND}}` | Full test suite command | `npm test` |
| `{{TEST_SINGLE_COMMAND}}` | Single file test command | `npx vitest run` |
| `{{SOURCE_STRUCTURE}}` | Feature/source directory layout | "src/features/<feature>/ for UI, services/api/ for backend" |
| `{{DB_PATTERN}}` | Database access pattern | "Factory functions with closures over DB client" |
| `{{BUILD_COMMAND}}` | Build command | `npm run build` |
| `{{COVERAGE_THRESHOLDS}}` | Coverage targets | "stmt=70, branch=65, fn=75, lines=70" |
| `{source_dir}` | Project source directory | `src/`, `lib/`, `app/` |
| `{features_dir}` | Feature directory pattern | `src/features/`, `app/domains/` |

**Replacement method — IMPORTANT:** Use the Read tool to load each installed file, perform substitutions in memory, then write the result back with the Write tool. Do NOT use `sed` for these replacements. BSD `sed` on macOS does not support multi-line replacement strings — values like `{{TECH_STACK}}` or `{{SOURCE_STRUCTURE}}` may contain newlines, which cause `sed` to misread the characters after the newline as flags and fail with `bad flag in substitute command`.

### Step 5: Write CLAUDE.md

**If the project already has a `CLAUDE.md` file:**

1. Read the existing `CLAUDE.md`.
2. Extract any project-specific content that the pipeline does not cover. Content to carry forward includes: tech stack, language/framework versions, test commands, lint/typecheck commands, build commands, file/directory structure, repo conventions, coding style rules, database patterns, CI/CD notes, environment setup, and any other project-specific facts. Do NOT carry forward content the pipeline now owns: agent behavior instructions, commit workflow, pipeline/QA process, or any "how Claude should behave" sections.
3. Rename the existing file: `mv CLAUDE.md CLAUDE.md.orig` (use the Bash tool).
4. Write a new `CLAUDE.md` containing: (a) any carried-forward project-specific sections, followed by (b) the pipeline section below.

**If no `CLAUDE.md` exists:** create one with the pipeline section only.

**Pipeline section:**

```markdown
## Pipeline System (Atelier Pipeline)

This project uses a multi-agent orchestration pipeline for structured development.

**Agents:** Eva (orchestrator), Robert (product), Sable (UX), Sarah (architect), Colby (engineer), Poirot, Agatha (docs), Ellis (commit)

**Commands:** /pm, /ux, /architect, /pipeline, /devops, /docs

**Pipeline state:** docs/pipeline/ -- Eva reads this at session start for recovery

**Key rules:**
- Colby writes tests when Sarah names a failure mode before Colby builds ()
- Poirot verifies every Colby output (no self-review)
- Ellis commits (Eva never runs git on code)
- Full test suite between work units
```

### Step 6: Print Summary and Offer Optional Features

After installation, print:

1. A count of files installed (37 mandatory files across 7 directories, plus any optional tech-stack references)
2. The directory tree showing what was created
3. The configured branching strategy and any CI recommendations
4. A reminder of available slash commands
5. Instructions to start their first pipeline run
6. **Offer optional features** -- Sentinel security agent, Agent Teams parallel execution, CI Watch automated CI monitoring, Claude Code Agent Resume prerequisite, and Atelier Brain persistent memory (Steps 6a through 6d)

**Example summary:**

```
Atelier Pipeline installed successfully.

Files installed: 36 (mandatory)
  .claude/rules/       -- 5 files (Eva persona, orchestration rules, pipeline operations, model selection, branch lifecycle)
  .claude/agents/      -- 9 files (Sarah, Colby, Robert, Sable, Poirot, Distillator, Ellis, Agatha)
  .claude/commands/    -- 6 files (/pm, /ux, /architect, /pipeline, /devops, /docs)
  .claude/references/  -- 6 files (quality framework, invocation templates, pipeline operations, agent preamble, branch/MR mode, telemetry metrics)
  .claude/hooks/       -- 6 files (path enforcement, sequencing, git guard, DoR/DoD warning, pre-compact, config)
  docs/pipeline/       -- 4 files (state tracking for session recovery)
  .claude/pipeline-config.json -- branching strategy configuration
  .claude/settings.json -- updated with hook registration
  CLAUDE.md            -- written fresh (project-specific content carried forward from CLAUDE.md.orig)

Branching strategy: [selected strategy]
  [CI template recommendations -- advisory, printed not written to files:
   - Trunk-based: Run CI on every push to main.
   - GitHub Flow: Run CI on MR events + push to main. Protect main.
   - GitLab Flow: Same + CI on push to staging/production. Protect all env branches.
   - GitFlow: CI on MR events for develop AND main. Protect both.]

Sentinel security agent: [enabled (Semgrep MCP) | not enabled]
Agent Teams: [enabled (experimental) | not enabled]
CI Watch: [enabled (max retries: N) | not enabled]
Compaction API: PreCompact hook installed for pipeline state preservation

Available commands:
  /pm          -- Feature discovery and product spec (Robert)
  /ux          -- UI/UX design (Sable)
  /architect   -- Architecture and ADR production (Sarah)
  /pipeline    -- Full pipeline orchestration (Eva)
  /devops      -- Infrastructure and deployment (Eva)
  /docs        -- Documentation planning and writing (Agatha)

To start your first pipeline:
  Describe a feature idea, or say "let's build [feature name]"
  Eva will size the work and route to the right starting agent.
```

### Step 6a: Sentinel Security Agent (Opt-In)

After printing the summary, offer the optional Sentinel security agent:

> Would you also like to enable **Sentinel** -- the security audit agent?
> It uses Semgrep to scan your code for vulnerabilities during QA.
> Requires the Semgrep MCP server (free). Optional -- the pipeline works fine without it.

**If user says yes:**

1. **Clean up legacy Sentinel install** (if present) — previous versions of pipeline-setup installed the deprecated `semgrep-mcp` PyPI package and registered it manually in `.mcp.json`. Check and clean up:
   - Run `command -v semgrep-mcp`. If found: run `pipx uninstall semgrep-mcp` (or `pip3 uninstall semgrep-mcp -y` if pipx is not available). Tell user: "Removed deprecated semgrep-mcp package — Sentinel now uses the official Semgrep plugin."
   - Check `.mcp.json` for a `"semgrep-mcp"` or `"semgrep"` entry that was manually added (command is `"semgrep-mcp"` or command is `"semgrep"` with args `["mcp"]`). If found: remove the entry. If `.mcp.json` is now empty (`{}` or `{"mcpServers": {}}`), delete the file.
   - This cleanup is safe to run even if the user never had the old install — all checks are no-ops when nothing is found.

2. **Check for Semgrep MCP** — verify the Semgrep MCP server is available. Run a quick check: `command -v semgrep && semgrep mcp --version`.
   - If not available, tell user: "Sentinel requires the Semgrep MCP server. Set it up with: `claude mcp add semgrep semgrep mcp` — then re-run `/pipeline-setup` to enable Sentinel." Skip Sentinel setup.
   - If semgrep is installed but not authenticated: tell user to run `semgrep login` first (opens browser, free account at https://semgrep.dev/login). Skip Sentinel setup.

3. Assemble `source/shared/agents/sentinel.md` + `source/claude/agents/sentinel.frontmatter.yml` to `.claude/agents/sentinel.md` (with placeholder customization, same as other agent personas).

4. Set `sentinel_enabled: true` in `.claude/pipeline-config.json`.

5. Update installation summary: "Sentinel security agent: enabled (Semgrep MCP)"

**If user says no:** Skip entirely. `sentinel_enabled` remains `false` in `pipeline-config.json`. Print: "Sentinel security agent: not enabled"

**Installation manifest addition (conditional):**

| Template Source | Destination | Install When |
|----------------|-------------|-------------|
| `source/shared/agents/sentinel.md` + `source/claude/agents/sentinel.frontmatter.yml` | `.claude/agents/sentinel.md` | User enables Sentinel in Step 6a (overlay assembly) |

### Step 6b: Agent Teams Opt-In (Experimental)

After the Sentinel offer (whether user said yes or no), offer the optional Agent Teams feature:

> Would you also like to enable **Agent Teams** -- experimental parallel wave execution?
> When Claude Code's Agent Teams feature is active (`CLAUDE_AGENT_TEAMS=1`), Eva can run
> multiple Colby build units in parallel using git worktrees. This is experimental and the
> pipeline works identically without it.

**If user says yes:**

1. Set `agent_teams_enabled: true` in `.claude/pipeline-config.json`.
2. Print: "Agent Teams: enabled (experimental). Set `CLAUDE_AGENT_TEAMS=1` in your environment
   to activate. The pipeline will fall back to sequential execution if the env var is unset."

**Idempotency:** If `agent_teams_enabled` already exists in `pipeline-config.json` and is `true`, skip the mutation and inform the user: "Agent Teams is already enabled." If it exists and is `false`, confirm with the user before changing.

**If user says no:** Skip entirely. `agent_teams_enabled` remains `false` in
`pipeline-config.json`. Print: "Agent Teams: not enabled"

**No dependency checks needed** -- unlike Sentinel (Semgrep MCP) or Brain (PostgreSQL), Agent Teams
has no external tools to install. The feature is entirely runtime-activated via the env var.

**No installation manifest expansion** -- Agent Teams uses the existing Colby persona
(`.claude/agents/colby.md`). No new files are installed.

### Step 6c: CI Watch Opt-In

After the Agent Teams offer (whether user said yes or no), offer the optional CI Watch feature:

> Would you also like to enable **CI Watch** -- automated post-push CI monitoring?
> After Ellis pushes, Eva watches your CI run and autonomously fixes failures via Poirot and Colby,
> pausing for your approval before pushing a fix. Requires `gh` (GitHub) or `glab` (GitLab) CLI.

**Platform CLI gate:** Read `platform_cli` from `.claude/pipeline-config.json`.
- If `platform_cli` is empty or missing, block with message: "CI Watch requires `gh` or `glab`. Configure a platform CLI first (run `/pipeline-setup` and set a platform)." Skip CI Watch setup.
- If `platform_cli` is set, continue.

**If user says yes:**

1. **Check CLI authentication:** run `gh auth status` (GitHub) or `glab auth status` (GitLab).
   - If auth check fails, tell user: "CI Watch requires an authenticated `{platform_cli}` session. Run `{platform_cli} auth login` first, then re-run `/pipeline-setup` to enable CI Watch." Skip CI Watch setup.

2. **Ask max retries:** "How many times should the fix cycle retry before stopping? (default: 3, minimum: 1)"
   - Accept an integer >= 1. If user presses Enter, use 3.

3. **Set config values:** in `.claude/pipeline-config.json`:
   - `ci_watch_enabled: true`
   - `ci_watch_max_retries: N` (the value from step 2)

4. **Compute and store platform commands** in `.claude/pipeline-config.json`:
   - `ci_watch_poll_command`: `gh run list --commit {sha} --json status,conclusion,url,databaseId --limit 1` (GitHub) or `glab ci list --branch {branch} -o json | head -1` (GitLab)
   - `ci_watch_log_command`: `gh run view {run_id} --log-failed | tail -200` (GitHub) or `glab ci trace {job_id} | tail -200` (GitLab)

5. Print: "CI Watch: enabled (max retries: N)"

**Idempotency:** If `ci_watch_enabled` already exists in `pipeline-config.json` and is `true`, skip the mutation and inform the user: "CI Watch is already enabled (max retries: {current_value})." If it exists and is `false`, confirm with the user before changing.

**If user says no:** Skip entirely. `ci_watch_enabled` remains `false` in `pipeline-config.json`. Print: "CI Watch: not enabled"

**No new agent files installed** -- CI Watch uses existing Poirot, Colby, and Ellis personas.

### Step 6d: Claude Code Agent Resume Prerequisite (Experimental)

After the CI Watch offer (whether user said yes or no), if the user is running Claude Code, offer one more experimental flag — ensure Claude Code's experimental
subagent-resume flag is enabled. This unlocks the `SendMessage` tool, which
the Agent tool advertises as the standard way to resume a spawned subagent
("use SendMessage with to: '<agentId>' to continue this agent"). Without
the flag, `SendMessage` is absent from the tool registry and every
follow-up to a subagent respawns a fresh agent that re-reads context from
scratch.

This is a Claude Code regression currently tracked at
[anthropics/claude-code#42737](https://github.com/anthropics/claude-code/issues/42737).
The atelier pipeline depends on cheap subagent resume for Sarah ADR
revisions, Colby rework cycles, and Poirot scoped re-runs.

**Check `~/.claude/settings.json` for the existing env var:**

```bash
jq -r '.env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS // empty' ~/.claude/settings.json
```

**If the value is already `1`, skip to the Brain setup offer.** (Idempotency.)

**Otherwise, always apply idempotently via jq:**

```bash
jq '. + {env: ((.env // {}) + {CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS: "1"})}' \
  ~/.claude/settings.json > ~/.claude/settings.json.tmp && \
  mv ~/.claude/settings.json.tmp ~/.claude/settings.json
```

Confirm: "`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set in `~/.claude/settings.json`. Restart Claude
Code for the change to take effect."

**No installation manifest expansion** -- this is a user-settings mutation,
not a pipeline file install.

**Brain plugin offer (conditional ask):**

After the Claude Code Agent Resume Prerequisite (Step 6d) offer (whether user said yes or no), check whether the user already has a brain plugin registered:

1. Probe ToolSearch for any tool name matching `mcp__*mybrain*` or `mcp__*atelier-brain__*` (suffix-match, so any plugin prefix is acceptable per ADR-0055).
2. If at least one match resolves: the user already has a brain plugin registered (either mybrain via the migration wizard in Step 0f, or an externally-installed equivalent). Print "Brain plugin already registered — skipping brain offer." Finish.
3. If no match resolves: the user has no brain plugin. Ask:

> The pipeline is ready. Would you also like to install the **mybrain** plugin?
> mybrain gives your agents persistent memory across sessions — architectural
> decisions, user corrections, QA lessons, and rejected alternatives survive
> when you close the terminal. It's optional and the pipeline works fine
> without it (per ADR-0055, the brain is now a separate plugin).

If the user says yes: print the install command and point them to the mybrain plugin's documentation:

```
Install mybrain in another terminal (or in this one after I finish):

  claude plugin install <mybrain-source-url>

See the mybrain plugin's README for the exact source URL. Once installed,
run `/brain-setup` from the mybrain plugin to configure the database
connection and provider settings.
```

If the user says no: print "OK — run `/pipeline-setup` again anytime if you change your mind. The pipeline runs fine without a brain plugin." Finish.

The pipeline-setup skill itself does NOT install or configure a brain — that responsibility moved to the standalone mybrain plugin in Phase 3 of ADR-0055.

### Step 7: Lightweight Reconfig

Users can change branching strategy without full reinstall by asking Eva to
"change branching strategy" or "switch to GitHub Flow".

**Procedure:**
1. Eva reads `.claude/pipeline-config.json`
2. Eva confirms no active pipeline. If active, return error: "Cannot change
   branching strategy mid-pipeline. Complete or abandon the current pipeline
   first."
3. Eva asks the new strategy question (same as Step 1b)
4. Eva rewrites `.claude/pipeline-config.json` and
   `.claude/rules/branch-lifecycle.md` only (installs the selected variant)
5. Eva announces the change and any new CI recommendations

No other files are modified during reconfig.

</procedure>

<gate id="setup-constraints">

## Important Notes

- **Do not overwrite existing files without asking.** If `.claude/rules/` or `.claude/agents/` already exists with content, ask the user whether to merge or replace.
- **Git-track the installed files.** Recommend the user commits the pipeline files so the system persists across clones and team members.
- **Templates are the source of truth.** If a template file is missing from the plugin's templates directory, report which file is missing and skip it rather than generating content from scratch.
- **Validate after install.** After writing all files, verify that Claude Code recognizes the slash commands by listing them. If the rules files are not being loaded, check that they are in `.claude/rules/` (Claude Code auto-loads all files in this directory).

</gate>

<section id="directory-map">

## What Each Directory Does

| Directory | Loaded By | Purpose |
|-----------|-----------|---------|
| `.claude/rules/` | Claude Code automatically (every conversation) | Eva persona and orchestration rules -- always active |
| `.claude/agents/` | Claude Code when subagents are invoked | Agent personas for execution tasks |
| `.claude/commands/` | Claude Code when user types a slash command | Manual agent invocation overrides |
| `.claude/references/` | Agents when they need shared knowledge | Quality framework, lessons, templates |
| `.claude/hooks/` | Claude Code on every tool call (PreToolUse) | Mechanical enforcement of agent boundaries, sequencing, and git operations |
| `docs/pipeline/` | Eva at session start | State recovery, context preservation, error tracking |

</section>
