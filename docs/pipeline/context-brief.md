# Context Brief

## Active Scope
ADR-0054 — Multi-Provider LLM Abstraction (Brain) and Pipeline Provider Routing. Medium pipeline.

## Compact Anchor
**Phase:** commit — all verification complete, Ellis pending.
**Feature:** ADR-0054 multi-provider brain abstraction + pipeline routing.
**Key decisions this session:**
- `brain/lib/llm-provider.mjs` (NEW): `embed()` + `chat()` with three adapter families (openai-compat, anthropic, local); anthropic normalizes response shape to openai-compat for uniform callers.
- Backward-compat shim pattern: all three refactored call sites (`embed.mjs`, `conflict.mjs`, `consolidation.mjs`) accept legacy string apiKey and coerce to openrouter providerConfig.
- `verifyEmbeddingDimension` wired at server startup with 5s non-blocking timeout race — warns, never halts.
- Hydrate scripts (`hydrate-telemetry.mjs`, `hydrate-enforcement.mjs`) updated to `buildProviderConfig` + `canEmbed` pattern — migration is now additive for non-OpenRouter providers.
- `model_provider` added to pipeline-config.json; translation table in pipeline-models.md (opus/sonnet/haiku × anthropic/bedrock/vertex).
- 11 code files + 3 doc files changed. 13/13 ADR-0054 tests, 388 total pass.
**Next step:** Ellis commit + ff-merge to main + worktree cleanup. Version bump (→ 4.2.0) as follow-on micro pipeline.

## Current State (for session-resume)
- **Phase:** idle. Architecture complete. ADR-0054 accepted. Next: Colby build.
- **ADR:** `docs/architecture/ADR-0054-multi-provider-llm-and-pipeline-routing.md`
- **Why this exists:** Brain hardcodes OpenRouter for all LLM calls; enterprise clients on GitHub Enterprise, Anthropic-direct, or air-gapped deployments cannot use the brain. Pipeline hardcodes Anthropic-direct model IDs; Bedrock/Vertex clients cannot route correctly.

## What Colby Builds

Full scope in pipeline-state.md Active Pipeline section. Three units.

**Key new/changed files:**
- `brain/lib/llm-provider.mjs` — NEW provider abstraction (embed + chat, three adapter families)
- `brain/lib/embed.mjs` — refactor line 32 (hardcoded OpenRouter fetch)
- `brain/lib/conflict.mjs` — refactor line 36 (hardcoded OpenRouter fetch); preserve apiKey injection
- `brain/lib/consolidation.mjs` — refactor hardcoded OpenRouter fetch
- `brain/lib/config.mjs` — add new config fields; backward compat via openrouter_api_key fallback
- `brain/server.mjs` — startup validation: anthropic cannot be embedding_provider
- `source/shared/pipeline/pipeline-config.json` — add model_provider field
- `source/shared/rules/pipeline-models.md` — add provider-shaped model ID translation table

**Adapter families:**
- `openai-compat`: OpenRouter (`openrouter.ai/api/v1`), OpenAI (`api.openai.com/v1`), GitHub Models (`models.github.ai/inference/v1`) — identical wire format, different base URL + Bearer auth
- `anthropic`: chat only — base `api.anthropic.com/v1`, `x-api-key` header, `content[0].text` response shape
- `local`: Ollama/LM Studio/llama.cpp — openai-compat at localhost, no auth required

**GitHub Models embedding specifics:**
- Endpoint: `POST https://models.github.ai/inference/embeddings`
- Auth: `Authorization: Bearer {GITHUB_TOKEN}`
- Required headers: `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2026-03-10`
- Model: `openai/text-embedding-3-small` (1536-dim confirmed)

**Local embedding default:**
- Model: `gte-qwen2-1.5b-instruct` (Ollama tag: `rjmalagon/gte-qwen2-1.5b-instruct-embed-f16`)
- 1536-dim native output, 3.6GB download, no schema migration needed

**Permanently excluded:** Voyage AI (user decision). Gemini (deferred — 768-dim, wrong wire format).

## How to Resume
Fresh Eva session reads pipeline-state.md + this file. Say "continue" or "build ADR-0054" to kick Colby.
Medium sizing — scout fan-out required before Colby per enforce-scout-swarm.sh.

---

## Parked — ADR-0053
**Feature:** Mechanical Brain Capture via Three-Hook Gate. Small pipeline.
**ADR:** `docs/architecture/ADR-0053-mechanical-brain-capture-gate.md`

**Why this exists:** type:agent SubagentStop hooks are silently broken in Claude Code 2.1.121 (GitHub #40010, 0 fires vs 9,006 for type:command). brain-extractor agent never ran. Three replacement hook types confirmed working empirically.

**What Colby builds:**
- `source/claude/hooks/enforce-brain-capture-pending.sh` — NEW (SubagentStop, writes pending file)
- `source/claude/hooks/enforce-brain-capture-gate.sh` — NEW (PreToolUse on Agent, blocks if pending)
- `source/claude/hooks/clear-brain-capture-pending.sh` — NEW (PostToolUse on agent_capture, clears)
- `source/claude/agents/brain-extractor.md` — DELETE
- `source/cursor/agents/brain-extractor.md` — DELETE
- `source/shared/references/pipeline-orchestration.md` — add escape-hatch protocol
- `.claude/settings.json` — remove type:agent entry, add PostToolUse entry

**Patterns:** SubagentStop writer → `log-agent-stop.sh`; PreToolUse gate → `enforce-scout-swarm.sh`; internal agent_type gating → `enforce-colby-stop-verify.sh`.

**Empirical evidence:** SubagentStop type:command: 9,006 fires confirmed. PreToolUse on Agent: operational. PostToolUse on agent_capture: confirmed 2026-04-28T15:44:06Z. type:agent: 0/1,591 events — broken (GitHub #40010).

**Resume:** Say "build ADR-0053" in a session after ADR-0054 ships.
