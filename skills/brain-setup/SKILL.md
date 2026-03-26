---
name: brain-setup
description: Use when users want to set up or connect to the Atelier Brain -- the persistent memory layer for the pipeline. Handles first-time setup (personal or shared), colleague onboarding from existing config, database provisioning, and connection verification.
---

# Atelier Brain -- Setup

This skill guides the user through setting up the Atelier Brain persistent memory layer. Run this conversationally -- ask questions one at a time, not as a list.

<protocol id="path-detection">

## Detection: Choose Path

Before asking anything, check whether a project-level brain config already exists:

1. Check if `.claude/brain-config.json` exists in the project root.
2. If it exists, go to **Path B -- Colleague Onboarding**.
3. If it does not exist, go to **Path A -- First-Time Setup**.

</protocol>

---

<procedure id="first-time-setup">

## Path A -- First-Time Setup

### Step 1: Personal or Shared

Ask the user:

> "Are you setting up a personal brain (local to you, not committed) or a shared team brain (committed to the repo)?"

- **Personal** -- config will be written to `${CLAUDE_PLUGIN_DATA}/brain-config.json` (never committed to git).
- **Shared** -- config will be written to `.claude/brain-config.json` (committed to the repo). All secrets stored as `${ENV_VAR}` references only -- never bare values.

### Step 2: Database Strategy

Ask the user:

> "How would you like to run the brain database -- local PostgreSQL, Docker, or remote PostgreSQL (RDS, Supabase, etc.)?"

#### Option: Docker

1. Verify Docker is installed by running `docker --version`.
   - **Not installed:** "Docker is not installed. Install it from https://docs.docker.com/get-docker/ and re-run this setup. Alternatively, choose local PostgreSQL."
2. Run: `docker compose -f ${CLAUDE_PLUGIN_ROOT}/brain/docker-compose.yml up -d`
3. Wait for the container to be healthy (poll `docker compose -f ${CLAUDE_PLUGIN_ROOT}/brain/docker-compose.yml ps` until status shows healthy, up to 30 seconds).
4. Schema auto-applies on first boot -- no manual step needed.
5. If the user chose **shared** setup, warn: "The Docker default password is not secure for team use. Set `ATELIER_BRAIN_DB_PASSWORD` as an environment variable for your team."
6. Database URL: `postgresql://atelier:${ATELIER_BRAIN_DB_PASSWORD}@localhost:5432/atelier_brain` (Docker default password is used if env var is not set).

#### Option: Local PostgreSQL

1. Verify PostgreSQL is running by running `pg_isready`.
   - **Not running:** "PostgreSQL does not appear to be running. Start it and re-run this setup."
2. Ask for the database name (default: `atelier_brain`).
3. Check if the database already exists by running `psql -lqt | grep <database_name>`.
   - **Exists:** Skip creation. Verify required tables exist by running `psql -d <database_name> -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"`. If tables are present, skip schema application.
   - **Does not exist:** Create the database and apply schema:
     ```
     createdb <database_name>
     psql -d <database_name> -f ${CLAUDE_PLUGIN_ROOT}/brain/schema.sql
     ```
4. Check for required extensions (pgvector, ltree) by running `psql -d <database_name> -c "SELECT extname FROM pg_extension;"`.
   - **Missing pgvector:** "The pgvector extension is required but not installed. Install it with: `brew install pgvector` (macOS) or `sudo apt install postgresql-16-pgvector` (Ubuntu). Then run `CREATE EXTENSION vector;` in your database."
   - **Missing ltree:** "The ltree extension is required but not installed. Run `CREATE EXTENSION ltree;` in your database (ltree ships with PostgreSQL)."
5. Database URL: `postgresql://<user>:${ATELIER_BRAIN_DB_PASSWORD}@localhost:5432/<database_name>`

#### Option: Remote PostgreSQL

1. Ask for connection details:
   - **Host** (e.g., `db.example.com`, `project.supabase.co`, `myinstance.us-east-1.rds.amazonaws.com`)
   - **Port** (default: `5432`)
   - **Database name** (default: `atelier_brain`)
   - **User** (default: `postgres`)
2. Ask if SSL is required:
   > "Should the connection use SSL? (Recommended yes for remote databases.)"
   - Default: **yes** for remote connections.
3. Verify the database is reachable by running `psql "postgresql://<user>:${ATELIER_BRAIN_DB_PASSWORD}@<host>:<port>/<database_name><ssl_params>" -c "SELECT 1;"`.
   - **Success:** Proceed.
   - **Connection refused / timed out:** "Cannot reach the database at `<host>:<port>`. Verify the host, port, and that your IP is allowed through any firewall or security group rules."
   - **Authentication error:** "Authentication failed. Check the username and `ATELIER_BRAIN_DB_PASSWORD` environment variable."
   - **SSL error:** "SSL connection failed. Verify that the remote database supports SSL and that your SSL mode is correct. Try `sslmode=require` or check if the provider requires a specific CA certificate."
4. Check if the schema is already applied by running `psql "<connection_url>" -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"`.
   - **Tables present:** Skip schema application.
   - **No tables:** Ask the user: "The database exists but has no tables. Apply the brain schema now?" If yes, run `psql "<connection_url>" -f ${CLAUDE_PLUGIN_ROOT}/brain/schema.sql`.
5. Check for required extensions (pgvector, ltree) by running `psql "<connection_url>" -c "SELECT extname FROM pg_extension;"`.
   - **Missing pgvector:** "The pgvector extension is required but not available on the remote database. Enable it through your provider's dashboard or run `CREATE EXTENSION vector;` if you have superuser access."
   - **Missing ltree:** "The ltree extension is required. Run `CREATE EXTENSION ltree;` on the remote database (ltree ships with PostgreSQL)."
6. Database URL: `postgresql://<user>:${ATELIER_BRAIN_DB_PASSWORD}@<host>:<port>/<database_name>?sslmode=require` (omit `?sslmode=require` if the user chose no SSL).

### Step 3: OpenRouter API Key

Ask the user:

> "Do you have an OpenRouter API key set in your environment (`OPENROUTER_API_KEY`), or would you like to provide one now?"

1. Check if `OPENROUTER_API_KEY` is set in the environment.
   - **Set:** "Found `OPENROUTER_API_KEY` in your environment."
   - **Not set:** Ask the user to provide one. Direct them to https://openrouter.ai/keys if needed. Instruct them to set it: `export OPENROUTER_API_KEY="sk-or-..."` in their shell profile.
2. For **shared** config, always store as `${OPENROUTER_API_KEY}` -- never the actual key value.
3. For **personal** config, store as `${OPENROUTER_API_KEY}` as well (the actual key lives in the environment, not in config files).

### Step 4: Scope Path

Ask the user:

> "What scope path should the brain use? This is a dot-separated namespace like `myorg.myproduct` that organizes your brain's knowledge."

Provide examples: `acme.webapp`, `myteam.api`, `personal.sideproject`.

### Step 4b: Brain Name (optional)

Ask the user:

> "Want to give your brain a name? This is a display name used in pipeline announcements and reports. Leave blank for the default ('Brain')."

Provide examples: `My Noodle`, `HAL`, `Cortex`, `The Archive`. Store as `brain_name` in the config. If the user skips or leaves blank, omit the field (defaults to "Brain").

### Step 5: Verify Connection

Run the `atelier_stats` tool (or equivalent health check endpoint) to verify the brain is reachable and functional.

- **Success:** Proceed to Step 6.
- **Failure -- connection refused:** "Cannot connect to the database. Verify it is running and the connection URL is correct."
- **Failure -- authentication error:** "Database credentials are incorrect. Check your password and try again."
- **Failure -- database does not exist:** "The database was not found. Verify the database name and that it was created successfully."

### Step 6: Write Config File

Write the config file based on the user's choice in Step 1.

**Config format:**

```json
{
  "database_url": "postgresql://atelier:${ATELIER_BRAIN_DB_PASSWORD}@localhost:5432/atelier_brain",
  "openrouter_api_key": "${OPENROUTER_API_KEY}",
  "scope": "myorg.myproduct",
  "brain_name": "My Noodle"
}
```

The `brain_name` field is optional. Omit it to default to "Brain".

For remote PostgreSQL, the URL includes the remote host and SSL parameters:

```json
{
  "database_url": "postgresql://postgres:${ATELIER_BRAIN_DB_PASSWORD}@db.example.com:5432/atelier_brain?sslmode=require",
  "openrouter_api_key": "${OPENROUTER_API_KEY}",
  "scope": "myorg.myproduct",
  "brain_name": "My Noodle"
}
```

- **Personal:** Write to `${CLAUDE_PLUGIN_DATA}/brain-config.json`. This path is local to the user and is not tracked by git.
- **Shared:** Write to `.claude/brain-config.json` in the project root. This file is committed to the repo. Verify that no bare secret values are present -- only `${ENV_VAR}` placeholders.

### Step 7: Enable Brain in Database

Set `brain_config.brain_enabled = true` in the database via `PUT /api/config`.

### Step 8: Confirm

Print a confirmation message:

```
Brain is live.
  Tools available: [N] (list count from atelier_stats)
  Scope: [scope path from Step 4]
  Config: [personal | shared] ([file path])
  Database: [Docker | Local PostgreSQL | Remote PostgreSQL]
```

</procedure>

---

<procedure id="colleague-onboarding">

## Path B -- Colleague Onboarding

This path runs when `.claude/brain-config.json` already exists in the project. The colleague does not need interactive setup -- they just need the right environment variables.

### Step 1: Read Existing Config

Read `.claude/brain-config.json` and extract the required environment variable references.

### Step 2: Check Environment Variables

Check which `${ENV_VAR}` references in the config are satisfied by the current environment:

- `OPENROUTER_API_KEY`
- `ATELIER_BRAIN_DB_PASSWORD` (if referenced in the database URL)
- Any other `${...}` placeholders found in the config

#### All present:

1. Verify the connection using `atelier_stats`.
2. Print: "Brain connected. You're using the team brain at [scope]."

#### Some missing:

Print:

```
Project brain config found at .claude/brain-config.json.

Set these environment variables to connect:
  - OPENROUTER_API_KEY    (not set)
  - ATELIER_BRAIN_DB_PASSWORD    (not set)

The pipeline will run in baseline mode until these are configured.
Add them to your shell profile or .env file (not committed to git).
```

### Step 3: No Further Interaction

Path B is non-interactive beyond env var guidance. Do not prompt for database setup, scope, or other configuration -- the shared config already has everything.

</procedure>

---

<gate id="security-constraints">

## Security Constraints

These rules are mandatory and never skippable:

1. **Shared config never contains bare secrets.** Only `${ENV_VAR}` placeholders. If you detect a bare API key or password in a shared config file, refuse to write it and ask the user to set an environment variable instead.
2. **Docker default password triggers a warning for team use.** If the user chose Docker + shared setup, always warn: "Set `ATELIER_BRAIN_DB_PASSWORD` for team use. The Docker default password is not secure for shared environments."
3. **Personal config is never committed to git.** It is written to `${CLAUDE_PLUGIN_DATA}/brain-config.json`, which is outside the project repo.

</gate>

<error-handling id="setup-errors">

## Error Handling

Handle these failure cases with clear messages and retry guidance:

| Error | Message |
|-------|---------|
| PostgreSQL not running | "PostgreSQL is not running. Start it with `brew services start postgresql` (macOS) or `sudo systemctl start postgresql` (Linux) and try again." |
| Docker not installed | "Docker is not installed. Install it from https://docs.docker.com/get-docker/ or choose local PostgreSQL instead." |
| Docker daemon not running | "Docker is installed but the daemon is not running. Start Docker Desktop (macOS) or run `sudo systemctl start docker` (Linux) and try again." |
| Wrong credentials | "Authentication failed. Check your database password and try again. For Docker setups, verify `ATELIER_BRAIN_DB_PASSWORD` matches what the container was started with." |
| pgvector not installed | "The pgvector extension is required for vector similarity search. Install: `brew install pgvector` (macOS) or `sudo apt install postgresql-16-pgvector` (Ubuntu). Then: `psql -d <db> -c 'CREATE EXTENSION vector;'`" |
| ltree not installed | "The ltree extension is required for scope hierarchy. Run: `psql -d <db> -c 'CREATE EXTENSION ltree;'` (ltree ships with PostgreSQL, no extra install needed)." |
| Database already exists | Skip creation. Verify tables exist. If tables are present, skip schema application and proceed. |
| Container fails to start | "The brain database container failed to start. Run `docker compose -f ${CLAUDE_PLUGIN_ROOT}/brain/docker-compose.yml logs` to see what went wrong." |
| Connection refused after setup | "The database started but is not accepting connections yet. Wait a few seconds and try again, or check the logs for errors." |
| SSL connection failed | "SSL connection to the remote database failed. Verify that the server supports SSL, check your `sslmode` setting, and confirm whether the provider requires a specific CA certificate (e.g., `sslmode=verify-full&sslrootcert=path/to/ca.pem`)." |
| Remote connection timed out | "Connection to `<host>:<port>` timed out. Check that the host and port are correct, your network can reach the server, and your IP is allowed through any firewall or security group rules." |

</error-handling>

<section id="setup-notes">

## Important Notes

- **This skill is conversational.** Ask questions one at a time. Do not dump all questions at once.
- **Do not skip verification.** Always run `atelier_stats` (or equivalent) before confirming setup is complete.
- **Respect existing state.** If a database already exists with tables, do not drop and recreate. Verify and proceed.
- **Scope path is required.** Do not default it silently -- always ask the user to confirm their scope.
- **Config file is the single source of truth.** All brain tools read from the config file at the path determined by the setup type (personal or shared).

</section>
