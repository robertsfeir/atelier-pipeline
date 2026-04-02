---
name: brain-uninstall
description: Use when users want to remove or disconnect the Atelier Brain persistent memory layer. Handles teardown for all database strategies (Docker, local PostgreSQL, remote PostgreSQL), config file removal, and offers a disconnect-only option that preserves the database.
---

# Atelier Brain -- Uninstall

This skill guides the user through removing or disconnecting the Atelier Brain persistent memory layer. Run this conversationally -- ask questions one at a time, not as a list. Present what will be removed BEFORE doing anything destructive.

<protocol id="config-detection">

## Detection: Locate Config

Before asking anything, find the brain config file:

1. Check if `.cursor/brain-config.json` exists in the project root (shared config).
2. Check if `${CURSOR_PLUGIN_DATA}/brain-config.json` exists (personal config).
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
   - **Config type:** personal (`${CURSOR_PLUGIN_DATA}`) or shared (`.cursor/`)
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
  brain/ directory            -- plugin code, not user data
```

If the config is shared (`.cursor/brain-config.json`), add:

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
The deletion of .cursor/brain-config.json needs to be committed to git.
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

1. Check if the Docker container is running:
   ```
   docker compose -f ${CURSOR_PLUGIN_ROOT}/brain/docker-compose.yml ps
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
   docker compose -f ${CURSOR_PLUGIN_ROOT}/brain/docker-compose.yml down
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

> Both a shared config (.cursor/brain-config.json) and a personal config
> exist. Remove both? (yes/no)

#### B4: Print Summary

```
Brain uninstalled.

Removed:
  Config:   [config file path(s)]
  Database: [what was done -- container removed, volume deleted/kept, database dropped, tables dropped, or "untouched"]

The brain/ directory in the plugin was NOT removed (it contains plugin code, not your data).
```

If shared config was removed:

```
The deletion of .cursor/brain-config.json needs to be committed to git.
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
- **Do NOT remove the `brain/` directory.** That directory contains the MCP server code (part of the plugin), not user data.
- **Do NOT remove the plugin itself.** This skill removes the brain config and optionally the database. The plugin remains installed.
- **Mask passwords in output.** When displaying database URLs, replace the password portion with `****`.
- **Shared config needs a commit.** When removing `.cursor/brain-config.json`, remind the user to commit the deletion.

</gate>

<error-handling id="uninstall-errors">

## Error Handling

Handle these failure cases with clear messages:

| Error | Message |
|-------|---------|
| No config file found | "No brain configuration found. Nothing to uninstall." |
| Docker not running | "Docker is not running. Cannot stop the container. Removing config file only. Stop the container manually later with: `docker compose -f ${CURSOR_PLUGIN_ROOT}/brain/docker-compose.yml down`" |
| Docker compose file missing | "Docker compose file not found. The container may have been set up differently. Removing config file only." |
| PostgreSQL not reachable | "PostgreSQL is not reachable. Cannot drop the database. Removing config file only. Drop it manually later with: `dropdb [database_name]`" |
| Remote database unreachable | "Cannot reach the remote database. Removing config file only. Clean up the remote tables manually when the database is available." |
| Permission denied on dropdb | "Permission denied when dropping the database. You may need to run this as a database superuser. Removing config file only." |
| Volume not found | "Docker volume `brain-data` not found. It may have already been removed. Proceeding with config removal." |
| Config file read error | "Cannot read the brain config file. It may be corrupted. Remove it manually at [path] and clean up the database using your database tools." |

</error-handling>
