---
name: brain-uninstall
description: Use when users want to remove or disconnect the mybrain plugin's persistent memory layer. Handles teardown for all database strategies (Docker, local PostgreSQL, remote PostgreSQL), config file removal, and offers a disconnect-only option that preserves the database.
---

# Brain Plugin -- Uninstall

This skill guides the user through removing or disconnecting the brain plugin's persistent memory layer. Per ADR-0055, the brain ships as a standalone `mybrain` plugin (separate from atelier-pipeline). This skill targets the brain config and database — it does NOT uninstall the mybrain plugin itself (use `claude plugin uninstall mybrain` for that). Run this conversationally -- ask questions one at a time, not as a list. Present what will be removed BEFORE doing anything destructive.

<contract>
  <requires>
    - At least one brain config file exists: `.claude/brain-config.json` (shared) or `${CLAUDE_PLUGIN_DATA}/brain-config.json` (personal).
    - Explicit user "yes" confirmation before any destructive action (config removal, container/volume removal, database drop, table drop).
    - For full-uninstall paths: matching tooling reachable for the chosen strategy (`docker` for Docker, `pg_isready` + `dropdb` for local, `psql` with credentials for remote).
  </requires>
  <produces>
    - Removal of `.claude/brain-config.json` and/or `${CLAUDE_PLUGIN_DATA}/brain-config.json`.
    - Optionally (Path B, per user choice): stopped/removed Docker container `brain-db`, deleted `brain-data` volume, dropped local database, or dropped public schema on remote.
  </produces>
  <invalidates>
    - `brain-hydrate` `<requires>`: brain is no longer reachable / `brain_enabled` no longer true after disconnect.
    - Pre-approved brain MCP tools in `permissions.allow` remain in `settings.json` but are inert until a new brain is configured (not removed by this skill).
  </invalidates>
</contract>

<protocol id="config-detection">

## Detection: Locate Config

Before asking anything, find the brain config file:

1. Check if `.claude/brain-config.json` exists in the project root (shared config).
2. Check if `${CLAUDE_PLUGIN_DATA}/brain-config.json` exists (personal config).
3. If **both** exist, note both. The shared config is the project-level config; the personal config is the user's local override.
4. If **neither** exists, stop:

> No brain configuration found. There is nothing to uninstall.
> If a brain was set up but the config was already removed, the database
> may still exist. Use your database tools directly to clean it up.

5. If a config file is found, read it to determine:
   - **Database strategy:** Infer from the `database_url` field:
     - Contains `localhost` with port `5432` and user `atelier` -- likely **Docker**
     - Contains `localhost` -- likely **Local PostgreSQL**
     - Contains a remote host -- **Remote PostgreSQL**
   - **Config type:** personal (`${CLAUDE_PLUGIN_DATA}`) or shared (`.claude/`)
   - **Scope:** from the `scope` field
   - **Brain name:** from the `brain_name` field (if present)

</protocol>

---

<procedure id="uninstall">

## Uninstall Procedure

### Step 1: Present Current Setup

Display what the brain setup looks like based on the config file:

```
Brain Uninstall -- Current Setup
================================

Config type:     [personal | shared]
Config location: [file path]
Database:        [Docker | Local PostgreSQL | Remote PostgreSQL]
Database URL:    [URL with password masked as ****]
Scope:           [scope path]
Brain name:      [name, or "Brain" if not set]
```

### Step 2: Offer Uninstall Options

Ask the user which level of removal they want:

> How would you like to proceed?
>
> 1. **Disconnect only** -- Remove the config file but leave the database untouched. The brain data stays intact and can be reconnected later.
> 2. **Full uninstall** -- Remove the config file AND clean up the database. Brain data will be permanently deleted.

Wait for the user's answer before proceeding.

---

### Path A -- Disconnect Only

This path removes the config file without touching the database.

#### A1: Present Removal Plan

```
Disconnect Plan
===============

WILL REMOVE:
  [config file path]    -- brain configuration file

WILL NOT TOUCH:
  Database at [masked URL]    -- data remains intact
  mybrain plugin              -- the plugin itself stays installed (use `claude plugin uninstall mybrain` to remove it)
```

If the config is shared (`.claude/brain-config.json`), add:

```
NOTE: This file is committed to git. You will need to commit the deletion.
```

#### A2: Get Confirmation

> Remove the config file? The database will remain untouched and can be
> reconnected by running brain-setup again. (yes/no)

**Do not proceed without explicit "yes" from the user.**

#### A3: Remove Config File

Delete the config file.

#### A4: Print Summary

```
Brain disconnected.

Removed: [config file path]
Database: untouched at [masked URL]

To reconnect later, run /brain-setup.
```

If shared config was removed:

```
The deletion of .claude/brain-config.json needs to be committed to git.
```

---

### Path B -- Full Uninstall

This path removes both the config file and cleans up the database. The procedure varies by database strategy.

#### B1: Data Loss Warning

Before anything else, warn clearly:

> **WARNING: This will permanently delete all brain data.**
>
> This includes all captured thoughts, decisions, patterns, lessons, and
> relations stored in the brain. This cannot be undone.
>
> The brain currently contains data under scope: [scope path]

#### B2: Database Cleanup (varies by strategy)

##### Docker

> **Note:** mybrain ships its own `docker-compose.yml` whose container and volume names may differ from the legacy bundled brain (`brain-db` / `brain-data`). Before running the commands below, inspect the mybrain compose file to confirm the actual names. The placeholders in this section reflect the legacy naming for users migrating from the bundled brain — substitute mybrain's actual container/volume names when applicable.

1. Check if the Docker container is running. The mybrain plugin ships its own `docker-compose.yml` (see the mybrain plugin's installation directory — typically `${CLAUDE_PLUGIN_DATA}/mybrain/docker-compose.yml` or wherever `claude plugin show mybrain` reports its files). Run:
   ```
   docker compose -f <mybrain-compose-path> ps
   ```

2. Present the Docker removal plan:

   ```
   Docker Cleanup Plan
   ===================

   WILL STOP AND REMOVE:
     Container: brain-db

   WILL REMOVE (config):
     [config file path]

   DOCKER VOLUME:
     brain-data    -- contains all brain database files
   ```

3. Ask about the Docker volume:

   > The Docker volume `brain-data` contains the actual database files.
   > Would you like to:
   > 1. **Delete the volume** -- Permanently removes all data
   > 2. **Keep the volume** -- Stops the container but preserves data on disk

4. Get explicit confirmation:

   If user chose to delete the volume:
   > This will stop the container, remove it, and delete all data in the
   > `brain-data` volume. Proceed? (yes/no)

   If user chose to keep the volume:
   > This will stop and remove the container but keep the data volume.
   > You can start a new container later that reattaches to this volume.
   > Proceed? (yes/no)

   **Do not proceed without explicit "yes" from the user.**

5. Execute:
   ```
   docker compose -f <mybrain-compose-path> down
   ```

   If user chose to delete the volume:
   ```
   docker volume rm brain-data
   ```

   If the container is not running or Docker is not available, skip container
   removal and note it:
   > Container was not running (or Docker is unavailable). Skipping container
   > cleanup. Proceeding with config removal.

##### Local PostgreSQL

1. Check if PostgreSQL is reachable by running `pg_isready`.

2. Extract the database name from the `database_url` in the config.

3. Ask the user:

   > The brain database `[database_name]` exists on your local PostgreSQL.
   > Would you like to:
   > 1. **Drop the database** -- Permanently deletes the database and all its data
   > 2. **Keep the database** -- Remove config only, leave the database in place

4. If user chose to drop:

   Get explicit confirmation:
   > This will run `dropdb [database_name]` which permanently deletes the
   > database and all data in it. Proceed? (yes/no)

   **Do not proceed without explicit "yes" from the user.**

   Execute:
   ```
   dropdb [database_name]
   ```

   If PostgreSQL is unreachable, skip the drop and inform the user:
   > PostgreSQL is not reachable. Cannot drop the database. Removing config
   > file only. You can drop the database manually later with:
   > `dropdb [database_name]`

5. If user chose to keep: proceed to config removal only.

##### Remote PostgreSQL

1. Extract the connection URL from the config.

2. Ask the user:

   > The brain uses a remote database at [host]:[port]/[database_name].
   > Would you like to:
   > 1. **Drop the brain tables** -- Remove all brain tables from the database but keep the database itself
   > 2. **Disconnect only** -- Remove config only, leave the remote database untouched

   Note: for remote databases, the skill drops tables rather than the entire
   database because the user may not own it or it may contain other data.

3. If user chose to drop tables:

   Get explicit confirmation:
   > This will drop all brain tables (thoughts, relations, config, etc.)
   > from the remote database. The database itself will remain. Proceed? (yes/no)

   **Do not proceed without explicit "yes" from the user.**

   Execute:
   ```
   psql "[connection_url]" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
   ```

   If the remote database is unreachable, skip the table drop and inform the user:
   > Cannot reach the remote database at [host]:[port]. Removing config file
   > only. You can clean up the remote tables manually later.

4. If user chose to disconnect: proceed to config removal only.

#### B3: Remove Config File

Delete the config file (same as Path A, Step A3).

If both a shared and personal config exist, remove both. Ask once:

> Both a shared config (.claude/brain-config.json) and a personal config
> exist. Remove both? (yes/no)

#### B4: Print Summary

```
Brain uninstalled.

Removed:
  Config:   [config file path(s)]
  Database: [what was done -- container removed, volume deleted/kept, database dropped, tables dropped, or "untouched"]

The mybrain plugin itself was NOT removed (this skill targets brain config + database only). To uninstall the mybrain plugin, run `claude plugin uninstall mybrain` separately.
```

If shared config was removed:

```
The deletion of .claude/brain-config.json needs to be committed to git.
```

If the database could not be reached:

```
The database could not be reached during uninstall. Config was removed.
To clean up the database manually:
  [Docker: docker compose -f ... down && docker volume rm brain-data]
  [Local: dropdb database_name]
  [Remote: psql "connection_url" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"]
```

To reconnect or set up a new brain later:

```
To set up a new brain later, run /brain-setup.
```

</procedure>

---

<gate id="uninstall-constraints">

## Important Notes

- **This skill is conversational.** Ask questions one at a time. Do not dump all options at once.
- **Never perform destructive actions without explicit confirmation.** Every database deletion (volume, database, tables) requires a separate "yes" from the user.
- **Present the plan before executing.** The user must see what will be removed before anything is touched.
- **Handle unreachable databases gracefully.** If the database cannot be reached, still remove the config file and provide manual cleanup instructions.
- **Do NOT remove the mybrain plugin itself.** This skill removes the brain config and optionally the database. The mybrain plugin remains installed (use `claude plugin uninstall mybrain` to remove it).
- **Mask passwords in output.** When displaying database URLs, replace the password portion with `****`.
- **Shared config needs a commit.** When removing `.claude/brain-config.json`, remind the user to commit the deletion.

</gate>

<error-handling id="uninstall-errors">

## Error Handling

Handle these failure cases with clear messages:

| Error | Message |
|-------|---------|
| No config file found | "No brain configuration found. Nothing to uninstall." |
| Docker not running | "Docker is not running. Cannot stop the container. Removing config file only. Stop the container manually later with: `docker compose -f <mybrain-compose-path> down` (find the path via `claude plugin show mybrain`)." |
| Docker compose file missing | "Docker compose file not found. The container may have been set up differently. Removing config file only." |
| PostgreSQL not reachable | "PostgreSQL is not reachable. Cannot drop the database. Removing config file only. Drop it manually later with: `dropdb [database_name]`" |
| Remote database unreachable | "Cannot reach the remote database. Removing config file only. Clean up the remote tables manually when the database is available." |
| Permission denied on dropdb | "Permission denied when dropping the database. You may need to run this as a database superuser. Removing config file only." |
| Volume not found | "Docker volume `brain-data` not found. It may have already been removed. Proceeding with config removal." |
| Config file read error | "Cannot read the brain config file. It may be corrupted. Remove it manually at [path] and clean up the database using your database tools." |

</error-handling>
