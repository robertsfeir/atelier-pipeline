---
name: brain-setup
description: Use when users want to set up or connect to the Atelier Brain -- the persistent memory layer for the pipeline. Auto-fixes existing config silently; guides new users through first-time setup.
---

# Atelier Brain -- Setup

This skill guides the user through setting up the Atelier Brain persistent memory layer. Run this conversationally -- ask questions one at a time, not as a list.

<contract>
  <requires>
    - Pipeline installed via `/pipeline-setup` (`.claude/` directory exists with `settings.json`).
    - PostgreSQL access via one of: Docker (`docker --version` + running daemon), local PostgreSQL (`pg_isready` succeeds), or a reachable remote PostgreSQL host with `pgvector` and `ltree` extensions available.
    - `ATELIER_BRAIN_DB_PASSWORD` set in the environment, plus the API-key env var that matches the chosen LLM provider family — `OPENROUTER_API_KEY` (default), `OPENAI_API_KEY`, `GITHUB_TOKEN` (GitHub Models), `ANTHROPIC_API_KEY` (chat only), or none for `local` (Ollama / LM Studio). Backward compatibility is preserved: a config containing only `openrouter_api_key` continues to work exactly as before.
    - `python3` (preferred) or `node` available on `PATH` for inline file mutations (Eva cannot use Write/Edit on `.claude/`).
  </requires>
  <produces>
    - `.claude/brain-config.json` (shared) or `${CLAUDE_PLUGIN_DATA}/brain-config.json` (personal) with `database_url`, `scope`, optional `brain_name`, and provider fields (`embedding_provider`, `embedding_model`, `embedding_api_key`, optional `embedding_base_url`; `chat_provider`, `chat_model`, `chat_api_key`, optional `chat_base_url`). Legacy `openrouter_api_key` is still accepted as a fallback when the user picks OpenRouter for both families. Secrets stored as `${ENV_VAR}` placeholders only.
    - `brain_config.brain_enabled = true` in the brain database via `PUT /api/config`.
    - `permissions.allow` in `.claude/settings.json` extended with the 8 atelier-brain MCP tool names.
    - Brain MCP tool schemas pre-loaded via ToolSearch for the current session.
  </produces>
  <invalidates>
    - Stale `atelier-brain` entry in project-level `.mcp.json` (removed in Step 0; the plugin now owns MCP registration).
  </invalidates>
</contract>

<protocol id="mcp-migration">

## Step 0: Remove Stale atelier-brain MCP Entry

Before asking anything, check for and clean up a stale `atelier-brain` entry in the project's `.mcp.json`.

1. Check if `.mcp.json` exists in the project root — if not, silent no-op, proceed to path-detection.
2. Check if `.mcpServers["atelier-brain"]` key exists — if not, silent no-op, proceed to path-detection.
3. If found: atomically remove atelier-brain and delete the file if mcpServers is empty. Run via Bash:

   ```bash
   python3 -c "
   import json, os
   p = '.mcp.json'
   if not os.path.exists(p): exit(0)
   try:
       d = json.load(open(p))
   except Exception:
       exit(0)  # malformed — leave for user to handle
   d.get('mcpServers', {}).pop('atelier-brain', None)
   if not d.get('mcpServers'):
       os.remove(p)
   else:
       json.dump(d, open(p, 'w'), indent=2)
   "
   ```

4. Safety-net check — after cleanup completes, run a final check: if `.mcp.json` exists and `mcpServers` is empty or absent, delete it unconditionally:

   ```bash
   if [ -f .mcp.json ]; then python3 -c "import json,os,sys; d=json.load(open('.mcp.json')); sys.exit(0) if d.get('mcpServers') else os.remove('.mcp.json')" 2>/dev/null; fi
   ```

5. Print: "Removed stale atelier-brain entry from .mcp.json — the plugin now handles MCP registration automatically."

   > **jq alternative (if Python unavailable):** `jq 'del(.mcpServers["atelier-brain"]) | if .mcpServers == {} then empty else . end' .mcp.json > .mcp.json.tmp && mv .mcp.json.tmp .mcp.json || rm -f .mcp.json`

</protocol>

---

<protocol id="path-detection">

## Detection: Choose Path

Before asking anything, check whether a project-level brain config already exists:

1. Run via Bash: `python3 -c "import os; print('exists' if os.path.exists('.claude/brain-config.json') else 'absent')"` (or equivalent).
2. If the file **exists** → go to **Path A: Auto-Fix**. Do not ask questions.
3. If the file **does not exist** → ask the user once:

   > "Would you like to add the Atelier Brain to this project? (yes/no)"

   - **Yes** → go to **Path B: First-Time Setup**.
   - **No** → print: "OK — run /brain-setup anytime to add it." Exit.

</protocol>

---

<procedure id="auto-fix">

## Path A: Auto-Fix

This path runs silently when `.claude/brain-config.json` already exists. Do not ask questions. Diagnose and print results.

### Step 1: Read Existing Config

Read the config using Bash:

```bash
python3 -c "import json; print(json.dumps(json.load(open('.claude/brain-config.json')), indent=2))"
```

Node fallback: `node -e "const fs=require('fs'); console.log(fs.readFileSync('.claude/brain-config.json','utf8'))"`

### Step 2: Scan for Placeholders

Scan all string values in the config for `${ENV_VAR}` patterns. Build a list of referenced environment variable names (e.g., `ATELIER_BRAIN_DB_PASSWORD`, `OPENROUTER_API_KEY`, any others).

### Step 3: Check Environment Variables

For each referenced variable, check whether it is set in the current environment:

```bash
python3 -c "
import json, os, re
config = json.load(open('.claude/brain-config.json'))
env_vars = re.findall(r'\$\{([^}]+)\}', json.dumps(config))
missing = [v for v in env_vars if not os.environ.get(v)]
for v in env_vars:
    print(v, 'SET' if os.environ.get(v) else 'MISSING')
"
```

Or use `printenv VAR_NAME` for individual checks.

If **any variable is missing**, skip Step 4 entirely. Go directly to Step 5 Case 2. Print: "Skipping connectivity check until environment variables are configured."

### Step 0 (Path A): Pre-load Brain MCP Tool Schemas

Brain MCP tool schemas are deferred — the first call to any `atelier_*` or `agent_*` tool without its schema loaded fails with `InputValidationError`. Run ToolSearch once before any brain call to load the schemas up front:

```
ToolSearch query: select:mcp__plugin_atelier-pipeline_atelier-brain__atelier_stats,mcp__plugin_atelier-pipeline_atelier-brain__agent_capture,mcp__plugin_atelier-pipeline_atelier-brain__agent_search,mcp__plugin_atelier-pipeline_atelier-brain__atelier_relation,mcp__plugin_atelier-pipeline_atelier-brain__atelier_browse,mcp__plugin_atelier-pipeline_atelier-brain__atelier_trace
```

Proceed to Step 4 only after ToolSearch returns.

### Step 4: Test Connectivity

(Only reached when all environment variables from Step 3 are SET.)

Run `atelier_stats` to test brain connectivity.

### Step 4b: Silently Merge Brain MCP Permissions

Run this without prompting. The merge is idempotent — tools already present are skipped.

```bash
python3 -c "
import json, os
settings_path = '.claude/settings.json'
if not os.path.exists(settings_path):
    print('settings.json not found — skipping permissions merge.')
else:
    tools = [
      'mcp__plugin_atelier-pipeline_atelier-brain__agent_capture',
      'mcp__plugin_atelier-pipeline_atelier-brain__agent_search',
      'mcp__plugin_atelier-pipeline_atelier-brain__atelier_stats',
      'mcp__plugin_atelier-pipeline_atelier-brain__atelier_hydrate',
      'mcp__plugin_atelier-pipeline_atelier-brain__atelier_hydrate_status',
      'mcp__plugin_atelier-pipeline_atelier-brain__atelier_browse',
      'mcp__plugin_atelier-pipeline_atelier-brain__atelier_relation',
      'mcp__plugin_atelier-pipeline_atelier-brain__atelier_trace',
    ]
    try:
        s = json.load(open(settings_path))
    except json.JSONDecodeError:
        print('settings.json is not valid JSON — skipping permissions merge. Check the file manually.')
        exit()
    s.setdefault('permissions', {})
    allow = s['permissions'].get('allow') or []
    s['permissions']['allow'] = allow
    added = [t for t in tools if t not in allow]
    allow.extend(added)
    if added:
        json.dump(s, open(settings_path, 'w'), indent=2)
        print(f'Added {len(added)} brain tool(s) to permissions.allow.')
"
```

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
Brain config found at .claude/brain-config.json.

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

- Docker setups: run `docker ps | grep atelier` to check container status. If container is stopped, print: "Run `docker compose -f ${CLAUDE_PLUGIN_ROOT}/brain/docker-compose.yml up -d` to restart the brain database."
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

### Step 0: Pre-load Brain MCP Tool Schemas

Brain MCP tool schemas are deferred — the first call to any `atelier_*` or `agent_*` tool without its schema loaded fails with `InputValidationError`. Run ToolSearch once before any brain call to load the schemas up front:

```
ToolSearch query: select:mcp__plugin_atelier-pipeline_atelier-brain__atelier_stats,mcp__plugin_atelier-pipeline_atelier-brain__agent_capture,mcp__plugin_atelier-pipeline_atelier-brain__agent_search,mcp__plugin_atelier-pipeline_atelier-brain__atelier_relation,mcp__plugin_atelier-pipeline_atelier-brain__atelier_browse,mcp__plugin_atelier-pipeline_atelier-brain__atelier_trace
```

Proceed to Step 1 only after ToolSearch returns.

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

### Step 3: LLM Provider Setup

Per ADR-0054, the brain supports multiple LLM provider families through three adapters (`openai-compat`, `anthropic`, `local`). The brain makes two kinds of LLM calls and you pick a provider for each: **embeddings** (used by every capture and search) and **chat** (used by conflict detection and consolidation synthesis). They can be the same provider or different ones.

Ask the user one question at a time -- embeddings first, then chat.

#### 3a. Embedding Provider

> "Which provider should the brain use for embeddings? Options:
> - **openrouter** (default, recommended) -- broad model selection, single key. Env var: `OPENROUTER_API_KEY`.
> - **github-models** -- recommended for GitHub Enterprise customers. Env var: `GITHUB_TOKEN`.
> - **local** -- Ollama or any OpenAI-compatible local endpoint. No API key. Default endpoint: `http://localhost:11434/v1`. Default model: `gte-qwen2-1.5b-instruct`.
> - **openai** -- direct OpenAI API. Env var: `OPENAI_API_KEY`.
>
> Press Enter for `openrouter`, or type one of: `openrouter`, `github-models`, `local`, `openai`."

Notes:
- `anthropic` is **not** offered for embeddings -- Anthropic has no embeddings API. The brain will reject this combination at startup.
- Default embedding model: `openai/text-embedding-3-small` (1536-dim). The brain enforces a 1536-dim probe at startup; if a chosen provider/model returns a different dimension, startup fails fast with remediation guidance.
- For non-default providers, ask whether they want to override `embedding_model` and/or `embedding_base_url`. Most users accept defaults.

Detect the relevant env var for the chosen provider:
- `openrouter` -> `OPENROUTER_API_KEY`. Direct to https://openrouter.ai/keys if missing.
- `github-models` -> `GITHUB_TOKEN`. Direct to https://github.com/settings/tokens if missing (a token with `read:packages` scope works).
- `openai` -> `OPENAI_API_KEY`. Direct to https://platform.openai.com/api-keys if missing.
- `local` -> no key needed; verify the endpoint is reachable.

#### 3b. Chat Provider

> "Which provider should the brain use for chat (conflict detection + consolidation)? Options:
> - **openrouter** (default) -- env var `OPENROUTER_API_KEY`.
> - **anthropic** -- direct Claude API. Env var: `ANTHROPIC_API_KEY`. Chat-only.
> - **github-models** -- env var `GITHUB_TOKEN`.
> - **openai** -- env var `OPENAI_API_KEY`.
> - **local** -- Ollama-compatible endpoint, no key.
>
> Press Enter for `openrouter`."

Default chat model: `openai/gpt-4o-mini`. Ask whether they want to override `chat_model` and/or `chat_base_url`. Most users accept defaults.

#### 3c. Backward Compatibility

If the user picks `openrouter` for both embeddings and chat, the resulting config is **identical to v3.x format** -- just `openrouter_api_key`, no new fields. Tell them: "If you choose OpenRouter for both, the config is backward-compatible with the single `openrouter_api_key` field." Existing v3.x configs continue to work with zero changes.

#### 3d. Storage Rules

1. For **shared** config, store keys as `${ENV_VAR}` placeholders -- never the actual key value.
2. For **personal** config, also store as `${ENV_VAR}` (the actual key lives in the environment).
3. The relevant env var is whichever the chosen provider expects (see 3a/3b above).

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

There are two valid shapes. The first is the v3.x backward-compatible shape (OpenRouter for both embeddings and chat). The second is the multi-provider shape introduced by ADR-0054. The brain accepts either; pick based on the choices made in Step 3.

**(a) Backward-compatible (OpenRouter for both):**

```json
{
  "database_url": "postgresql://atelier:${ATELIER_BRAIN_DB_PASSWORD}@localhost:5432/atelier_brain",
  "openrouter_api_key": "${OPENROUTER_API_KEY}",
  "scope": "myorg.myproduct",
  "brain_name": "My Noodle"
}
```

**(b) Multi-provider (e.g., Anthropic chat + GitHub Models embeddings):**

```json
{
  "database_url": "postgresql://atelier:${ATELIER_BRAIN_DB_PASSWORD}@localhost:5432/atelier_brain",
  "embedding_provider": "github-models",
  "embedding_api_key": "${GITHUB_TOKEN}",
  "chat_provider": "anthropic",
  "chat_api_key": "${ANTHROPIC_API_KEY}",
  "scope": "myorg.myproduct",
  "brain_name": "My Noodle"
}
```

All ADR-0054 fields are optional. Omitted fields fall back to defaults: `embedding_provider`/`chat_provider` default to `openrouter`; `embedding_model` defaults to `openai/text-embedding-3-small`; `chat_model` defaults to `openai/gpt-4o-mini`. `embedding_base_url` and `chat_base_url` default to the chosen provider's canonical endpoint and only need to be set for self-hosted or proxied deployments (e.g., a local Ollama server). `embedding_api_key`/`chat_api_key` may be omitted when `openrouter_api_key` is set and the provider is `openrouter` -- the brain falls back to it.

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
#   Personal: PATH = os.path.expandvars('\${CLAUDE_PLUGIN_DATA}')   # Claude
#             PATH = os.path.expandvars('\${CURSOR_PLUGIN_DATA}')   # Cursor
#   Shared:   PATH = '.claude'                                      # Claude
#             PATH = '.cursor'                                      # Cursor
PATH = 'REPLACE_ME'  # set to one of the values above before running
if not PATH or PATH == 'REPLACE_ME':
    raise ValueError('PATH must be set before running this snippet — see comments above.')

config = {
  'database_url': 'COMPUTED_URL',
  # Backward-compatible default (OpenRouter for both embeddings and chat):
  'openrouter_api_key': '\${OPENROUTER_API_KEY}',
  # Multi-provider (ADR-0054) -- replace the line above with the fields below
  # when Step 3 chose anything other than openrouter for either operation:
  # 'embedding_provider': 'github-models',
  # 'embedding_api_key': '\${GITHUB_TOKEN}',
  # 'chat_provider': 'anthropic',
  # 'chat_api_key': '\${ANTHROPIC_API_KEY}',
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
//   Personal: const PATH = process.env.CLAUDE_PLUGIN_DATA;   // Claude
//             const PATH = process.env.CURSOR_PLUGIN_DATA;   // Cursor
//   Shared:   const PATH = '.claude';                        // Claude
//             const PATH = '.cursor';                        // Cursor
const PATH = 'REPLACE_ME'; // set to one of the values above before running
if (!PATH || PATH === 'REPLACE_ME') { console.error('PATH must be set before running this snippet — see comments above.'); process.exit(1); }

const config = {
  database_url: 'COMPUTED_URL',
  // Backward-compatible default (OpenRouter for both embeddings and chat):
  openrouter_api_key: '\${OPENROUTER_API_KEY}',
  // Multi-provider (ADR-0054) -- replace the line above with the fields below
  // when Step 3 chose anything other than openrouter for either operation:
  // embedding_provider: 'github-models',
  // embedding_api_key: '\${GITHUB_TOKEN}',
  // chat_provider: 'anthropic',
  // chat_api_key: '\${ANTHROPIC_API_KEY}',
  scope: 'COMPUTED_SCOPE',
  // brain_name: 'BRAIN_NAME',  // optional -- omit to default to 'Brain'
};
const configPath = path.join(PATH, 'brain-config.json');
fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
console.log(\`Config written to \${configPath}.\`);
"
```

- **Personal:** Write to `${CLAUDE_PLUGIN_DATA}/brain-config.json`. This path is local to the user and is not tracked by git.
- **Shared:** Write to `.claude/brain-config.json` in the project root. This file is committed to the repo. Verify that no bare secret values are present -- only `${ENV_VAR}` placeholders.

### Step 7: Enable Brain in Database

Set `brain_config.brain_enabled = true` in the database via `PUT /api/config`.

### Step 8: Pre-approve Brain MCP Tools

To allow the brain to work without interruption (including in background hook agents), I'll add the atelier-brain tools to your project's `permissions.allow` in `.claude/settings.json`. This means Claude Code won't prompt you each time a brain tool is called.

**Idempotency check:** Read `.claude/settings.json` using Bash and check whether all 8 tools below are already present in `permissions.allow`. If all 8 are already present, skip this step silently and proceed to Step 9.

Read using Bash:

```bash
python3 -c "
import json, os
p = '.claude/settings.json'
if not os.path.exists(p):
    print('settings.json not found.')
else:
    print(json.dumps(json.load(open(p)), indent=2))
"
```

The tools to be added:

- `mcp__plugin_atelier-pipeline_atelier-brain__agent_capture`
- `mcp__plugin_atelier-pipeline_atelier-brain__agent_search`
- `mcp__plugin_atelier-pipeline_atelier-brain__atelier_stats`
- `mcp__plugin_atelier-pipeline_atelier-brain__atelier_hydrate`
- `mcp__plugin_atelier-pipeline_atelier-brain__atelier_hydrate_status`
- `mcp__plugin_atelier-pipeline_atelier-brain__atelier_browse`
- `mcp__plugin_atelier-pipeline_atelier-brain__atelier_relation`
- `mcp__plugin_atelier-pipeline_atelier-brain__atelier_trace`

Ask the user:

> "Add these to permissions.allow? (Recommended yes)"

- **If yes (or accepted):** Merge the 8 tool names into `permissions.allow` (dedup -- skip any already present) and write the file back using Bash:

  ```bash
  python3 -c "
  import json
  tools = [
    'mcp__plugin_atelier-pipeline_atelier-brain__agent_capture',
    'mcp__plugin_atelier-pipeline_atelier-brain__agent_search',
    'mcp__plugin_atelier-pipeline_atelier-brain__atelier_stats',
    'mcp__plugin_atelier-pipeline_atelier-brain__atelier_hydrate',
    'mcp__plugin_atelier-pipeline_atelier-brain__atelier_hydrate_status',
    'mcp__plugin_atelier-pipeline_atelier-brain__atelier_browse',
    'mcp__plugin_atelier-pipeline_atelier-brain__atelier_relation',
    'mcp__plugin_atelier-pipeline_atelier-brain__atelier_trace',
  ]
  try:
      s = json.load(open('.claude/settings.json'))
  except FileNotFoundError:
      print('settings.json not found — skipping permissions merge.')
      exit()
  except json.JSONDecodeError:
      print('settings.json is not valid JSON — cannot merge permissions. Check the file manually.')
      exit()
  s.setdefault('permissions', {})
  allow = s['permissions'].get('allow') or []
  s['permissions']['allow'] = allow
  added = [t for t in tools if t not in allow]
  allow.extend(added)
  json.dump(s, open('.claude/settings.json', 'w'), indent=2)
  print(f'Added {len(added)} tool(s) to permissions.allow.')
  "
  ```

- **If no:** Note: "Brain tools will require manual approval on each call. Background captures via the brain-extractor hook may be silently blocked."

### Step 9: Confirm

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
3. **Personal config is never committed to git.** It is written to `${CLAUDE_PLUGIN_DATA}/brain-config.json`, which is outside the project repo.
4. **Do not use Write or Edit tools.** brain-setup runs on Eva's main thread where `enforce-eva-paths` blocks Write/Edit outside `docs/pipeline/`. ALL file operations (reading/writing brain-config.json, modifying .mcp.json, writing settings.json) MUST use the Bash tool via python3 or node inline commands.

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
