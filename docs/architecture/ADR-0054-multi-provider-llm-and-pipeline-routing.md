# ADR-0054: Multi-Provider LLM Abstraction (Brain) and Pipeline Provider Routing

## Status
Accepted.

## Context

Two related coupling problems block enterprise adoption.

**Brain.** The Atelier Brain MCP server hardcodes every LLM call to OpenRouter. `brain/lib/embed.mjs:32` posts to `https://openrouter.ai/api/v1/embeddings` with `openai/text-embedding-3-small`; `brain/lib/conflict.mjs:36` and `brain/lib/consolidation.mjs` post to `https://openrouter.ai/api/v1/chat/completions` with `openai/gpt-4o-mini`. Authentication flows through `OPENROUTER_API_KEY` resolved in `brain/lib/config.mjs:91`. Clients on GitHub Enterprise, Anthropic-direct, or air-gapped deployments cannot use the brain without proxying through OpenRouter, which several of them are contractually unable to do.

**Pipeline.** The pipeline's tier table in `.claude/rules/pipeline-models.md` resolves logical names (opus/sonnet/haiku) to Anthropic-direct model IDs and assumes Claude Code is configured against `api.anthropic.com`. Clients standardised on Bedrock or Vertex have working credentials in their Claude Code environment but no way to tell the pipeline to emit Bedrock-shaped or Vertex-shaped model IDs.

The two decisions share the same motivation -- give a single deployment independent control over (a) where the brain calls embeddings, (b) where the brain calls chat completions, and (c) where the pipeline routes its agent invocations -- so they belong in one ADR.

A planning session with the user established the substantive choices already; this ADR records them.

## Options Considered

**Option A: Per-call-site provider configuration.** Add provider config inline at each fetch in embed.mjs, conflict.mjs, consolidation.mjs. Cheapest diff, but every new provider touches three files and the call sites diverge over time. Rejected -- it ratifies the existing duplication.

**Option B: Single provider abstraction in the brain + a pipeline-level model_provider field.** Introduce `brain/lib/llm-provider.mjs` exposing `embed(text)` and `chat(messages)`; refactor the three call sites to it; add `model_provider` to `pipeline-config.json` with a translation table in `pipeline-models.md`. Embedding and chat providers configure independently so a deployment can mix (e.g. GitHub Models for embeddings, Anthropic for chat). Three adapter families cover the matrix: `openai-compat` (OpenRouter, OpenAI direct, GitHub Models -- identical wire format, different base URL + auth header), `anthropic` (chat only -- different auth header and response shape), and `local` (Ollama / LM Studio / llama.cpp at localhost via openai-compat). This is what was decided.

**Option C: Adopt a third-party LLM SDK (LiteLLM, Vercel AI SDK, etc.).** Solves the abstraction problem but pulls in a substantial dependency, a translation layer the brain doesn't need, and an upgrade cadence the brain doesn't control. The matrix we actually have to support is small (three adapter families). Rejected as oversized.

## Decision

Add `brain/lib/llm-provider.mjs` exporting `embed(text)` and `chat(messages)`. Refactor `embed.mjs`, `conflict.mjs`, and `consolidation.mjs` to call through it. Configure embedding provider and chat provider independently via `brain-config.json` (or env), each selecting one of three adapter families: `openai-compat`, `anthropic` (chat only), `local`. Voyage AI is permanently excluded; Gemini is deferred (768-dim incompatible with the existing `vector(1536)` schema, non-OpenAI wire format).

Add `model_provider` to `source/shared/pipeline/pipeline-config.json` with values `anthropic` (default), `bedrock`, `vertex`. The logical-name to provider-shaped model ID translation lives in `.claude/rules/pipeline-models.md`. Credentials remain in the Claude Code environment configuration -- the pipeline emits IDs, it does not hold keys.

Anthropic has no embeddings API. Clients selecting `anthropic` for chat must pair it with a zero-migration embedding provider (OpenRouter, OpenAI direct, GitHub Models, or local). `brain-setup` enforces this pairing at install time and verifies the embedding provider's actual output dimension via a test embed call; on dimension mismatch it offers a schema migration rather than silently failing on insert.

GitHub Models (`models.github.ai`) is the recommended embedding provider for Anthropic-chat enterprise clients already on GitHub Enterprise -- it serves `openai/text-embedding-3-small` at 1536-dim with a GitHub PAT carrying `models:read`.

For the local adapter family, the recommended default model is `gte-qwen2-1.5b-instruct` (Ollama tag: `rjmalagon/gte-qwen2-1.5b-instruct-embed-f16`) -- a 1.5B-parameter, ~3.6GB model with fixed 1536-dim native output. No schema migration is required for the local path. The `brain-setup` dimension check still runs (defence in depth against future model swaps), but the expected result on the recommended local default is 1536.

Colby writes a behavioral test for the embedding-dimension check in `brain-setup` because a silent dimension drift would corrupt every subsequent insert and only surface as a downstream similarity-search failure.

### Factual Claims

- `brain/lib/embed.mjs` calls `https://openrouter.ai/api/v1/embeddings` directly at line 32.
- `brain/lib/conflict.mjs` calls `https://openrouter.ai/api/v1/chat/completions` directly at line 36 with `openai/gpt-4o-mini`.
- `brain/lib/consolidation.mjs` is the third OpenRouter chat-completions call site.
- `EMBEDDING_MODEL` constant lives in `brain/lib/config.mjs:48` as `openai/text-embedding-3-small`.
- `brain/lib/config.mjs:91` resolves `OPENROUTER_API_KEY` from env as the only auth path when no config file is found.
- The brain schema defines `vector(1536)` for the `embedding` column; any provider returning a different dimension requires migration.
- `source/shared/pipeline/pipeline-config.json` does not currently contain a `model_provider` field.
- `.claude/rules/pipeline-models.md` table maps tiers to logical names (opus/sonnet/haiku); it does not currently encode provider-shaped model IDs.
- `brain/lib/conflict.mjs` and `embed.mjs` both receive `apiKey` as a function parameter -- the abstraction must preserve that injection point or replace it consistently across all three call sites.

### LOC Estimate

~250 lines changed across ~7 files (new `brain/lib/llm-provider.mjs`, three brain refactors, `config.mjs` additions, `pipeline-config.json` field, `pipeline-models.md` translation table). Order of magnitude only.

## Rationale

Option B beats A because the abstraction collapses the matrix: adding a provider in the same family is a config row, not a call-site edit. It beats C because the actual surface is small (two operations, three adapter families) and a vendored SDK would carry features the brain will never exercise.

Independent embedding/chat configuration is load-bearing. Anthropic-chat clients have no other choice -- Anthropic ships no embeddings API -- and forcing them to also host their own embedding provider would gate adoption on infra they don't have. Pairing Anthropic chat with GitHub Models embeddings is the path of least resistance for the enterprise clients already asking for it.

Voyage AI exclusion is a user decision, not a coverage gap. Gemini is deferred because the 768-dim incompatibility is a schema problem, not an adapter problem -- adding it without a dimension-aware schema would silently corrupt inserts.

If the brain switches to a chat provider that returns a non-1536 embedding dimension on the embedding side without `brain-setup` catching it, every conflict-detection insert proceeds with a vector the schema will reject or, worse, accept with truncation. The dimension check at install time exists specifically because that failure mode is silent at the application layer.

**Rollback sketch.** The brain abstraction is additive -- if `llm-provider.mjs` proves wrong, the three call sites can be restored from git in one revert. The pipeline `model_provider` field defaults to `anthropic`, so existing deployments are unaffected until they opt in. No DB schema change ships in this ADR; the dimension-aware migration is a separate decision when Gemini or another non-1536 provider gets prioritised.

## Falsifiability

This decision is wrong if either of the following holds after rollout:

1. The brain cannot start with each supported provider configured and successfully embed a test string end-to-end (provider selected, auth resolved, dimension verified, embedding stored).
2. The pipeline does not route to Bedrock-shaped model IDs when `model_provider: bedrock` is set in `pipeline-config.json`, or to Vertex-shaped IDs when `vertex` is set.

Either failure means the abstraction did not absorb the variation it was built to absorb, and we revisit -- likely toward Option C.

## Sources

- `brain/lib/embed.mjs:32` -- hardcoded OpenRouter embeddings endpoint.
- `brain/lib/conflict.mjs:36` -- hardcoded OpenRouter chat-completions endpoint.
- `brain/lib/config.mjs:48,91` -- embedding model constant and OpenRouter key resolution.
- `source/shared/pipeline/pipeline-config.json` -- pipeline config target for `model_provider` field.
- `.claude/rules/pipeline-models.md` -- tier/agent assignment table that gains the translation rows.
