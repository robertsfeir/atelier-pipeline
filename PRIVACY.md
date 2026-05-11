# Privacy policy

## Overview

atelier-pipeline is a Claude Code plugin consisting of bash hook scripts, markdown
agent persona files, and skills. It runs entirely on your local machine inside
your Claude Code session. The plugin reads files in your project's working tree
and writes session state files to `docs/pipeline/` within that project. It does
not run any remote service, does not collect analytics, and does not transmit
data to the plugin author or any third party.

## Data this plugin transmits

**None, beyond what Claude Code already transmits.**

Every file read and every prompt exchanged during a Claude Code session flows
through Claude Code's normal tool-use loop to Anthropic's API. That data flow
exists regardless of whether atelier-pipeline is installed and is governed by
Anthropic's own privacy policy and Claude Code terms of service, not by this
plugin. atelier-pipeline adds no additional transmission path.

## Local data

The plugin reads and writes data only on your machine:

- **Reads:** files in your project working tree that agents need to complete
  their tasks (source code, specs, ADRs, existing docs).
- **Writes:** session state files in `docs/pipeline/` — `pipeline-state.md`,
  `context-brief.md`, `error-patterns.md`, `investigation-ledger.md`,
  `last-qa-report.md`. These files stay in your project directory.
- **Hook stdin:** Claude Code passes tool-call JSON to PreToolUse hook scripts
  via stdin. The hooks evaluate that input locally and exit; they do not
  forward it anywhere.

Nothing written by this plugin leaves your machine.

## Optional companion plugin: mybrain

atelier-pipeline works in baseline mode without any additional dependencies. An
optional companion plugin, **mybrain** (separate install, separate repository,
separate marketplace listing), adds persistent memory backed by a
user-managed Postgres database.

When mybrain is installed and configured:

- Content you choose to store is sent to a user-configured embedding provider
  (such as OpenRouter or a local Ollama instance) to compute vector embeddings.
- Those embeddings and associated text are stored in a Postgres database you
  control — local Docker, a native Postgres install, or your own RDS instance.
- The embedding provider you configure governs how that data is handled. Review
  its privacy policy separately.

atelier-pipeline itself does not read or write to mybrain's database directly;
it calls mybrain's MCP tools, which run in a separate Node.js process you start
and manage. If mybrain is not installed, none of the above applies.

mybrain repository: https://github.com/robertsfeir/mybrain

## Third-party services

atelier-pipeline does not integrate with or transmit data to any third-party
service. The plugin has no analytics, no error reporting, and no update
telemetry.

## Contact

Questions about this policy: **robert@sfeir.dev**

## Updates

This policy may be updated alongside plugin releases; changes are noted in
CHANGELOG entries.
