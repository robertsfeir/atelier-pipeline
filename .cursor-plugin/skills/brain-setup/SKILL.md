---
name: brain-setup
description: Use when users want to set up or connect to the Atelier Brain -- the persistent memory layer for the pipeline. Auto-fixes existing config silently; guides new users through first-time setup.
---

# Atelier Brain -- Setup

This skill guides the user through setting up the Atelier Brain persistent memory layer. Run this conversationally -- ask questions one at a time, not as a list.

<protocol id="mcp-migration">

## Step 0: Remove Stale atelier-brain MCP Entry

Before asking anything, check for and clean up a stale `atelier-brain` entry in the project's `.mcp.json`.

1. Check if `.mcp.json` exists in the project root — if not, silent no-op, proceed to path-detection.
2. Check if `.mcpServers["atelier-brain"]` key exists — if not, silent no-op, proceed to path-detection.
3. If found: remove it with `jq 'del(.mcpServers["atelier-brain"])' .mcp.json > .mcp.json.tmp && mv .mcp.json.tmp .mcp.json`
4. If the resulting `.mcpServers` object is empty (`{}`), delete `.mcp.json` entirely.
5. Print: "Removed stale atelier-brain entry from .mcp.json — the plugin now handles MCP registration automatically."
6. If jq is unavailable: run via Bash:

   ```bash
   python3 -c "
   import json, os
   if not os.path.exists('.mcp.json'): exit(0)
   d = json.load(open('.mcp.json'))
   d.get('mcpServers', {}).pop('atelier-brain', None)
   if 'mcpServers' in d and not d.get('mcpServers'):
       os.remove('.mcp.json')
   else:
       json.dump(d, open('.mcp.json', 'w'), indent=2)
   "
   ```

   Node fallback: `node -e "const fs=require('fs');if(!fs.existsSync('.mcp.json'))process.exit(0);const d=JSON.parse(fs.readFileSync('.mcp.json'));if(d.mcpServers){delete d.mcpServers['atelier-brain'];}if(d.mcpServers&&Object.keys(d.mcpServers).length===0){fs.unlinkSync('.mcp.json');}else{fs.writeFileSync('.mcp.json',JSON.stringify(d,null,2));}"`

</protocol>

---

<protocol id="path-detection">

## Detection: Choose Path

Before asking anything, check whether a brain config already exists in either of the two possible locations:

1. Run via Bash:

   ```bash
   python3 -c "
   import os
   shared = '.cursor/brain-config.json'
   personal = os.path.expandvars('\${CURSOR_PLUGIN_DATA}/brain-config.json')
   print('shared' if os.path.exists(shared) else ('personal' if os.path.exists(personal) else 'absent'))
   "
   ```

2. If **shared** (`shared`) → resolved config path is `.cursor/brain-config.json` → go to **Path A: Auto-Fix**.
3. If **personal** → resolved config path is `${CURSOR_PLUGIN_DATA}/brain-config.json` → go to **Path A: Auto-Fix**.
4. If **absent** → ask the user once:

   > "Would you like to add the Atelier Brain to this project? (yes/no)"

   - **Yes** → go to **Path B: First-Time Setup**.
   - **No** → print: "OK — run /brain-setup anytime to add it." Exit.

In Path A, pass the **resolved config path** (whichever was found) into all subsequent steps. Do not hardcode `.cursor/brain-config.json`.

</protocol>

---

<procedure id="auto-fix">

## Path A: Auto-Fix

This path runs silently when a brain config was found during path-detection. Do not ask questions. Diagnose and print results. Use the **resolved config path** from path-detection throughout this procedure.

### Step 1: Read Existing Config

Read the config using Bash, substituting the resolved config path:

```bash
python3 -c "import json; print(json.dumps(json.load(open('RESOLVED_CONFIG_PATH')), indent=2))"
```

Node fallback: `node -e "const fs=require('fs'); console.log(fs.readFileSync('RESOLVED_CONFIG_PATH','utf8'))"`

(Replace `RESOLVED_CONFIG_PATH` with the actual path determined in path-detection: either `.cursor/brain-config.json` for shared or the expanded `${CURSOR_PLUGIN_DATA}/brain-config.json` for personal.)

### Step 2: Scan for Placeholders

Scan all string values in the config for `${ENV_VAR}` patterns. Build a list of referenced environment variable names (e.g., `ATELIER_BRAIN_DB_PASSWORD`, `OPENROUTER_API_KEY`, any others).

### Step 3: Check Environment Variables

For each referenced variable, check whether it is set in the current environment:

```bash
python3 -c "
import json, os, re
config = json.load(open('RESOLVED_CONFIG_PATH'))
env_vars = re.findall(r'\$\{([^}]+)\}', json.dumps(config))
missing = [v for v in env_vars if not os.environ.get(v)]
for v in env_vars:
    print(v, 'SET' if os.environ.get(v) else 'MISSING')
"
```

Or use `printenv VAR_NAME` for individual checks.

If **any variable is missing**, skip Step 4 entirely. Go directly to Step 5 Case 2. Print: "Skipping connectivity check until environment variables are configured."

### Step 4: Test Connectivity

(Only reached when all environment variables from Step 3 are SET.)

Run `atelier_stats` to test brain connectivity.

### Step 4b: Tool Pre-Approval Note

> Cursor manages tool permissions differently from Claude Code — there is no `settings.json`-based pre-approval mechanism. If brain tools prompt for approval on each call, check your Cursor plugin settings and ensure the `atelier-pipeline` plugin is trusted. This is a one-time action in Cursor's UI.

### Step 5: Evaluate and Report

**Case 1 — All env vars present AND `atelier_stats` succeeds:**

Print:

```
Brain connected. [scope from config] — [N] tools available.
```

Done. No further action.

**Case 2 — Env vars missing (Step 4 was skipped):**

List every missing variable by name. Print:

```
Brain config found at [resolved config path from path-detection].

The following environment variables are not set:
  - ATELIER_BRAIN_DB_PASSWORD    (not set)
  - OPENROUTER_API_KEY    (not set)

Connectivity check skipped — environment variables must be set first.
The pipeline will run in baseline mode until these are configured.
Add them to your shell profile (e.g., ~/.zshrc or ~/.bash_profile):
  export ATELIER_BRAIN_DB_PASSWORD="..."
  export OPENROUTER_API_KEY="sk-or-..."
```

Done. No further action.

**Case 3 — All env vars present BUT `atelier_stats` fails:**

Print the specific error from `atelier_stats`. Then check database status:

- Docker setups: run `docker ps | grep atelier` to check container status. If container is stopped, print: "Run `docker compose -f ${CURSOR_PLUGIN_ROOT}/brain/docker-compose.yml up -d` to restart the brain database."
- Local PostgreSQL: run `pg_isready` to check if PostgreSQL is running. If not: "PostgreSQL is not running. Start it with `brew services start postgresql` (macOS) or `sudo systemctl start postgresql` (Linux)."
- Remote: check if the host is reachable with the command below. If not: "Cannot reach the remote database. Check your network and firewall rules."

  > Replace `HOST` and `PORT` with the actual host and port extracted from `database_url` in the config before running this command.

  `python3 -c "import socket; s=socket.create_connection(('HOST', PORT), timeout=5); s.close(); print('reachable')"`

Print targeted remediation based on what was found. Do not ask questions.

Done. No further action.

</procedure>

---

<procedure id="first-time-setup">

## Path B: First-Time Setup

### Step 1: Personal or Shared

Ask the user:

> "Are you setting up a personal brain (local to you, not committed) or a shared team brain (committed to the repo)?"

- **Personal** -- config will be written to `${CURSOR_PLUGIN_DATA}/brain-config.json` (never committed to git).
- **Shared** -- config will be written to `.cursor/brain-config.json` (committed to the repo). All secrets stored as `${ENV_VAR}` references only -- never bare values.

### Step 2: Database Strategy

Ask the user:

> "How would you like to run the brain database -- local PostgreSQL, Docker, or remote PostgreSQL (RDS, Supabase, etc.)?"

#### Option: Docker

1. Verify Docker is installed by running `docker --version`.
   - **Not installed:** "Docker is not installed. Install it from https://docs.docker.com/get-docker/ and re-run this setup. Alternatively, choose local PostgreSQL."
2. Run: `docker compose -f ${CURSOR_PLUGIN_ROOT}/brain/docker-compose.yml up -d`
3. Wait for the container to be healthy (poll `docker compose -f ${CURSOR_PLUGIN_ROOT}/brain/docker-compose.yml ps` until status shows healthy, up to 30 seconds).
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
     psql -d <database_name> -f ${CURSOR_PLUGIN_ROOT}/brain/schema.sql
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
   - **No tables:** Ask the user: "The database exists but has no tables. Apply the brain schema now?" If yes, run `psql "<connection_url>" -f ${CURSOR_PLUGIN_ROOT}/brain/schema.sql`.
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

Derive a smart default from the project directory: take the last segment of the current working directory and append `.app` (e.g., `/Users/sfeirr/projects/clairvoyant` becomes `clairvoyant.app`). Present this as a suggested default the user can accept or override.

Ask the user:

> "What scope path should the brain use? This is a dot-separated namespace like `myorg.myproduct` that organizes your brain's knowledge. Based on your project directory, I'd suggest: `{derived-default}` — press Enter to accept or type your own."

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

Write the config file using Bash. Do not use Write or Edit tools.

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

**Write using python3:**

```bash
python3 -c "
import json, os

# Choose PATH based on setup type from Step 1:
#   Personal: PATH = os.path.expandvars('\${CURSOR_PLUGIN_DATA}')   # Cursor
#             PATH = os.path.expandvars('\${CLAUDE_PLUGIN_DATA}')   # Claude
#   Shared:   PATH = '.cursor'                                      # Cursor
#             PATH = '.claude'                                      # Claude
PATH = 'REPLACE_ME'  # set to one of the values above before running
if not PATH or PATH == 'REPLACE_ME':
    raise ValueError('PATH must be set before running this snippet — see comments above.')

config = {
  'database_url': 'COMPUTED_URL',
  'openrouter_api_key': '\${OPENROUTER_API_KEY}',
  'scope': 'COMPUTED_SCOPE',
  # 'brain_name': 'BRAIN_NAME',  # optional -- omit to default to 'Brain'
}
config_path = os.path.join(PATH, 'brain-config.json')
json.dump(config, open(config_path, 'w'), indent=2)
print(f'Config written to {config_path}.')
"
```

**Node fallback:**

```bash
node -e "
const fs = require('fs');
const path = require('path');

// Choose PATH based on setup type from Step 1:
//   Personal: const PATH = process.env.CURSOR_PLUGIN_DATA;   // Cursor
//             const PATH = process.env.CLAUDE_PLUGIN_DATA;   // Claude
//   Shared:   const PATH = '.cursor';                        // Cursor
//             const PATH = '.claude';                        // Claude
const PATH = 'REPLACE_ME'; // set to one of the values above before running
if (!PATH || PATH === 'REPLACE_ME') { console.error('PATH must be set before running this snippet — see comments above.'); process.exit(1); }

const config = {
  database_url: 'COMPUTED_URL',
  openrouter_api_key: '\${OPENROUTER_API_KEY}',
  scope: 'COMPUTED_SCOPE',
  // brain_name: 'BRAIN_NAME',  // optional -- omit to default to 'Brain'
};
const configPath = path.join(PATH, 'brain-config.json');
fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
console.log(\`Config written to \${configPath}.\`);
"
```

- **Personal:** Write to `${CURSOR_PLUGIN_DATA}/brain-config.json`. This path is local to the user and is not tracked by git.
- **Shared:** Write to `.cursor/brain-config.json` in the project root. This file is committed to the repo. Verify that no bare secret values are present -- only `${ENV_VAR}` placeholders.

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

<gate id="security-constraints">

## Security Constraints

These rules are mandatory and never skippable:

1. **Shared config never contains bare secrets.** Only `${ENV_VAR}` placeholders. If you detect a bare API key or password in a shared config file, refuse to write it and ask the user to set an environment variable instead.
2. **Docker default password triggers a warning for team use.** If the user chose Docker + shared setup, always warn: "Set `ATELIER_BRAIN_DB_PASSWORD` for team use. The Docker default password is not secure for shared environments."
3. **Personal config is never committed to git.** It is written to `${CURSOR_PLUGIN_DATA}/brain-config.json`, which is outside the project repo.
4. **Use Bash for all file operations.** All file modifications (writing brain-config.json, modifying .mcp.json) must be performed via Bash inline commands (python3 or node) rather than relying on IDE tool calls, which may not have access to the correct working directory or environment context.

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
| Container fails to start | "The brain database container failed to start. Run `docker compose -f ${CURSOR_PLUGIN_ROOT}/brain/docker-compose.yml logs` to see what went wrong." |
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
