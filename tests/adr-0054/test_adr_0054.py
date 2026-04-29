"""Behavioral and structural tests for ADR-0054.

Multi-Provider LLM Abstraction (Brain) and Pipeline Provider Routing.

These tests cover the eight points listed in the ADR-0054 build constraints:

(a) llm-provider.mjs exports embed and chat (and verifyEmbeddingDimension).
(b) config.mjs backward compat: brain-config with only `openrouter_api_key`
    still produces a valid providerConfig for both embed and chat.
(c) anthropic embedding rejection: the brain rejects anthropic as
    embedding_provider at the buildProviderConfig + llm-provider boundary.
(d) `model_provider` field is present in source/shared/pipeline/pipeline-config.json.
(e) Bedrock-shaped model IDs are present in pipeline-models.md.
(f) Vertex-shaped model IDs are present in pipeline-models.md.
(g) `local` adapter family in llm-provider.mjs uses a localhost base URL.
(h) Dimension check behavioral test: verifyEmbeddingDimension surfaces a
    mismatch as `{ ok: false, actual, expected, message }`.

The Node-side behavioral tests are run via `node --eval` from Python -- this
keeps the suite inside the project's pytest gate (see CLAUDE.md test command)
without forcing a separate Node test runner orchestration.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BRAIN_DIR = PROJECT_ROOT / "brain"
LLM_PROVIDER = BRAIN_DIR / "lib" / "llm-provider.mjs"
CONFIG_MJS = BRAIN_DIR / "lib" / "config.mjs"
PIPELINE_CONFIG = PROJECT_ROOT / "source" / "shared" / "pipeline" / "pipeline-config.json"
PIPELINE_MODELS = PROJECT_ROOT / "source" / "shared" / "rules" / "pipeline-models.md"


def _node_available() -> bool:
    return shutil.which("node") is not None


def _run_node_script(script: str) -> tuple[int, str, str]:
    """Run a Node.js inline script. Returns (returncode, stdout, stderr)."""
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    return proc.returncode, proc.stdout, proc.stderr


# ─── (a) llm-provider exports embed, chat, verifyEmbeddingDimension ───────


def test_llm_provider_file_exists() -> None:
    """ADR-0054 (a): llm-provider.mjs is created at brain/lib/llm-provider.mjs."""
    assert LLM_PROVIDER.exists(), f"Expected file at {LLM_PROVIDER}"


@pytest.mark.skipif(not _node_available(), reason="node not on PATH")
def test_llm_provider_exports_embed_chat_verify() -> None:
    """ADR-0054 (a): llm-provider.mjs exports embed, chat, verifyEmbeddingDimension."""
    script = textwrap.dedent(
        """
        const m = await import('./brain/lib/llm-provider.mjs');
        const required = ['embed', 'chat', 'verifyEmbeddingDimension'];
        const missing = required.filter(k => typeof m[k] !== 'function');
        if (missing.length) {
          console.error('MISSING:' + missing.join(','));
          process.exit(1);
        }
        console.log('OK');
        """
    ).strip()
    rc, out, err = _run_node_script(script)
    assert rc == 0, f"node exited {rc}: stdout={out!r} stderr={err!r}"
    assert "OK" in out


# ─── (b) config.mjs backward compat ──────────────────────────────────────


@pytest.mark.skipif(not _node_available(), reason="node not on PATH")
def test_buildProviderConfig_backward_compat_openrouter_only() -> None:
    """ADR-0054 (b): a config with only `openrouter_api_key` resolves both
    embed and chat to a valid OpenRouter providerConfig with the historical
    defaults. No new keys required for v3.x configs to keep working.
    """
    script = textwrap.dedent(
        """
        const { buildProviderConfig } = await import('./brain/lib/config.mjs');
        const legacyConfig = { openrouter_api_key: 'sk-or-test-legacy' };

        const embedCfg = buildProviderConfig(legacyConfig, 'embed');
        const chatCfg = buildProviderConfig(legacyConfig, 'chat');

        const out = { embedCfg, chatCfg };
        console.log(JSON.stringify(out));
        """
    ).strip()
    rc, out, err = _run_node_script(script)
    assert rc == 0, f"node exited {rc}: stderr={err!r}"
    payload = json.loads(out.strip())

    embed_cfg = payload["embedCfg"]
    chat_cfg = payload["chatCfg"]

    assert embed_cfg["family"] == "openai-compat"
    assert embed_cfg["baseUrl"].startswith("https://openrouter.ai")
    assert embed_cfg["apiKey"] == "sk-or-test-legacy"
    assert embed_cfg["model"] == "openai/text-embedding-3-small"
    assert embed_cfg["providerName"] == "openrouter"

    assert chat_cfg["family"] == "openai-compat"
    assert chat_cfg["baseUrl"].startswith("https://openrouter.ai")
    assert chat_cfg["apiKey"] == "sk-or-test-legacy"
    assert chat_cfg["model"] == "openai/gpt-4o-mini"
    assert chat_cfg["providerName"] == "openrouter"


# ─── (c) anthropic embedding rejection ───────────────────────────────────


@pytest.mark.skipif(not _node_available(), reason="node not on PATH")
def test_llm_provider_rejects_anthropic_embedding() -> None:
    """ADR-0054 (c): llm-provider.embed() raises when family is anthropic.

    Anthropic ships no embeddings API; the abstraction must surface that as a
    clear configuration error, not a silent 404 from the provider.
    """
    script = textwrap.dedent(
        """
        const { embed } = await import('./brain/lib/llm-provider.mjs');
        const providerConfig = {
          family: 'anthropic',
          baseUrl: 'https://api.anthropic.com/v1',
          apiKey: 'sk-ant-test',
          model: 'claude-haiku-4-5-20251001',
        };
        try {
          await embed('hello', providerConfig);
          console.log('UNEXPECTED_SUCCESS');
        } catch (err) {
          console.log('REJECTED:' + err.message);
        }
        """
    ).strip()
    rc, out, err = _run_node_script(script)
    assert rc == 0, f"node exited {rc}: stderr={err!r}"
    assert "REJECTED:" in out
    assert "anthropic" in out.lower()
    assert "embedding" in out.lower()


@pytest.mark.skipif(not _node_available(), reason="node not on PATH")
def test_buildProviderConfig_anthropic_embed_resolves_anthropic_family() -> None:
    """ADR-0054 (c) sister-test: when a user sets `embedding_provider: "anthropic"`
    in brain-config.json, buildProviderConfig returns family="anthropic". The
    actual rejection happens at the llm-provider boundary (the test above)
    AND at server.mjs startup. This test pins the contract that
    buildProviderConfig does not silently rewrite the family.
    """
    script = textwrap.dedent(
        """
        const { buildProviderConfig } = await import('./brain/lib/config.mjs');
        const cfg = { embedding_provider: 'anthropic', anthropic_api_key: 'sk-ant-x' };
        const embedCfg = buildProviderConfig(cfg, 'embed');
        console.log(JSON.stringify(embedCfg));
        """
    ).strip()
    rc, out, err = _run_node_script(script)
    assert rc == 0, f"node exited {rc}: stderr={err!r}"
    embed_cfg = json.loads(out.strip())
    assert embed_cfg["family"] == "anthropic"
    assert embed_cfg["providerName"] == "anthropic"


# ─── (d) pipeline-config.json contains model_provider ─────────────────────


def test_pipeline_config_has_model_provider_field() -> None:
    """ADR-0054 (d): source/shared/pipeline/pipeline-config.json contains
    `model_provider` with the default value `anthropic`.
    """
    raw = PIPELINE_CONFIG.read_text(encoding="utf-8")
    data = json.loads(raw)
    assert "model_provider" in data, (
        "pipeline-config.json must include a `model_provider` field "
        "(see ADR-0054). Default should be `anthropic` for backward compat."
    )
    assert data["model_provider"] == "anthropic", (
        f"Default model_provider must be `anthropic`, got {data['model_provider']!r}"
    )


# ─── (e) Bedrock model IDs present in pipeline-models.md ─────────────────


def test_pipeline_models_contains_bedrock_ids() -> None:
    """ADR-0054 (e): pipeline-models.md contains Bedrock-shaped model IDs.

    Bedrock IDs follow the pattern `anthropic.claude-{family}-{ver}-{date}-v1:0`.
    """
    text = PIPELINE_MODELS.read_text(encoding="utf-8")
    expected = [
        "anthropic.claude-opus-4-7-20250514-v1:0",
        "anthropic.claude-sonnet-4-6-20250514-v1:0",
        "anthropic.claude-haiku-4-5-20251001-v1:0",
    ]
    for needle in expected:
        assert needle in text, (
            f"Missing Bedrock model ID {needle!r} in pipeline-models.md "
            "(ADR-0054 translation table)."
        )


# ─── (f) Vertex model IDs present in pipeline-models.md ──────────────────


def test_pipeline_models_contains_vertex_ids() -> None:
    """ADR-0054 (f): pipeline-models.md contains Vertex-shaped model IDs.

    Vertex IDs follow the pattern `claude-{family}@NNN`.
    """
    text = PIPELINE_MODELS.read_text(encoding="utf-8")
    expected = [
        "claude-opus@002",
        "claude-sonnet@001",
        "claude-haiku@001",
    ]
    for needle in expected:
        assert needle in text, (
            f"Missing Vertex model ID {needle!r} in pipeline-models.md "
            "(ADR-0054 translation table)."
        )


# ─── (g) local adapter uses localhost base URL ───────────────────────────


@pytest.mark.skipif(not _node_available(), reason="node not on PATH")
def test_local_adapter_uses_localhost_base_url() -> None:
    """ADR-0054 (g): the `local` adapter family resolves to a localhost URL
    by default (Ollama on :11434 is the recommended path).
    """
    script = textwrap.dedent(
        """
        const { DEFAULT_BASE_URL } = await import('./brain/lib/llm-provider.mjs');
        console.log(DEFAULT_BASE_URL.local);
        """
    ).strip()
    rc, out, err = _run_node_script(script)
    assert rc == 0, f"node exited {rc}: stderr={err!r}"
    base_url = out.strip()
    assert "localhost" in base_url, (
        f"local adapter base URL must contain 'localhost', got {base_url!r}"
    )
    assert base_url.startswith("http://"), (
        f"local adapter must default to plain http, got {base_url!r}"
    )


@pytest.mark.skipif(not _node_available(), reason="node not on PATH")
def test_local_adapter_omits_auth_header_when_no_apikey() -> None:
    """ADR-0054 (g) sister-test: the local adapter does not emit an
    Authorization header when apiKey is null/empty. This is what allows
    Ollama / LM Studio / llama.cpp to accept calls from the brain without
    any auth setup. Verified by intercepting fetch() in-process.
    """
    script = textwrap.dedent(
        """
        const { embed } = await import('./brain/lib/llm-provider.mjs');
        let captured = null;
        globalThis.fetch = async (url, options) => {
          captured = { url, options };
          return {
            ok: true,
            json: async () => ({ data: [{ embedding: new Array(1536).fill(0.1) }] }),
            text: async () => '',
          };
        };
        const providerConfig = {
          family: 'local',
          baseUrl: 'http://localhost:11434/v1',
          apiKey: null,
          model: 'rjmalagon/gte-qwen2-1.5b-instruct-embed-f16',
        };
        await embed('hello', providerConfig);
        const headerKeys = Object.keys(captured.options.headers).map(k => k.toLowerCase());
        const hasAuth = headerKeys.includes('authorization');
        console.log(JSON.stringify({ url: captured.url, hasAuth }));
        """
    ).strip()
    rc, out, err = _run_node_script(script)
    assert rc == 0, f"node exited {rc}: stderr={err!r}"
    payload = json.loads(out.strip())
    assert payload["url"] == "http://localhost:11434/v1/embeddings"
    assert payload["hasAuth"] is False, (
        "local adapter must NOT emit Authorization header when apiKey is null"
    )


# ─── (h) Dimension check behavioral test ─────────────────────────────────


@pytest.mark.skipif(not _node_available(), reason="node not on PATH")
def test_verify_embedding_dimension_detects_mismatch() -> None:
    """ADR-0054 (h): verifyEmbeddingDimension surfaces a mismatch as
    { ok: false, actual, expected, message }.

    The ADR calls out that a silent dimension drift would corrupt every
    subsequent insert. This test pins the validator's behavior on the
    failure path (provider returns 768-dim, schema expects 1536-dim).
    """
    script = textwrap.dedent(
        """
        const { verifyEmbeddingDimension } = await import('./brain/lib/llm-provider.mjs');
        // Mock fetch to return a 768-dim embedding -- the Gemini-shaped failure
        // mode the ADR explicitly calls out.
        globalThis.fetch = async () => ({
          ok: true,
          json: async () => ({ data: [{ embedding: new Array(768).fill(0.0) }] }),
          text: async () => '',
        });
        const providerConfig = {
          family: 'openai-compat',
          baseUrl: 'https://example.test/v1',
          apiKey: 'sk-test',
          model: 'fake-768-dim',
        };
        const result = await verifyEmbeddingDimension(providerConfig, 1536);
        console.log(JSON.stringify(result));
        """
    ).strip()
    rc, out, err = _run_node_script(script)
    assert rc == 0, f"node exited {rc}: stderr={err!r}"
    result = json.loads(out.strip())
    assert result["ok"] is False
    assert result["actual"] == 768
    assert result["expected"] == 1536
    assert "mismatch" in result["message"].lower()


@pytest.mark.skipif(not _node_available(), reason="node not on PATH")
def test_verify_embedding_dimension_passes_on_match() -> None:
    """ADR-0054 (h) sister-test: verifyEmbeddingDimension reports ok=true
    when the provider returns the expected dimension. Without this, a
    paranoid validator could fail closed on the happy path.
    """
    script = textwrap.dedent(
        """
        const { verifyEmbeddingDimension } = await import('./brain/lib/llm-provider.mjs');
        globalThis.fetch = async () => ({
          ok: true,
          json: async () => ({ data: [{ embedding: new Array(1536).fill(0.0) }] }),
          text: async () => '',
        });
        const providerConfig = {
          family: 'openai-compat',
          baseUrl: 'https://example.test/v1',
          apiKey: 'sk-test',
          model: 'openai/text-embedding-3-small',
        };
        const result = await verifyEmbeddingDimension(providerConfig, 1536);
        console.log(JSON.stringify(result));
        """
    ).strip()
    rc, out, err = _run_node_script(script)
    assert rc == 0, f"node exited {rc}: stderr={err!r}"
    result = json.loads(out.strip())
    assert result["ok"] is True
    assert result["actual"] == 1536
    assert result["expected"] == 1536


# ─── Bonus: github-models adapter sets required headers ──────────────────


@pytest.mark.skipif(not _node_available(), reason="node not on PATH")
def test_github_models_adapter_sets_required_headers() -> None:
    """ADR-0054: GitHub Models requires `Accept: application/vnd.github+json`
    and `X-GitHub-Api-Version: 2026-03-10`. Without these the inference
    endpoint rejects the call. This test pins those headers so a future
    refactor cannot silently drop them.
    """
    script = textwrap.dedent(
        """
        const { embed } = await import('./brain/lib/llm-provider.mjs');
        const { buildProviderConfig } = await import('./brain/lib/config.mjs');
        const cfg = buildProviderConfig(
          { embedding_provider: 'github-models', github_token: 'ghp_test' },
          'embed',
        );
        let captured = null;
        globalThis.fetch = async (url, options) => {
          captured = { url, options };
          return {
            ok: true,
            json: async () => ({ data: [{ embedding: new Array(1536).fill(0.1) }] }),
            text: async () => '',
          };
        };
        await embed('probe', cfg);
        const headers = captured.options.headers;
        const headersLower = Object.fromEntries(
          Object.entries(headers).map(([k, v]) => [k.toLowerCase(), v]),
        );
        console.log(JSON.stringify({
          url: captured.url,
          accept: headersLower['accept'],
          apiVersion: headersLower['x-github-api-version'],
          auth: headersLower['authorization'],
        }));
        """
    ).strip()
    rc, out, err = _run_node_script(script)
    assert rc == 0, f"node exited {rc}: stderr={err!r}"
    payload = json.loads(out.strip())
    assert "models.github.ai" in payload["url"]
    assert payload["accept"] == "application/vnd.github+json"
    assert payload["apiVersion"] == "2026-03-10"
    assert payload["auth"] == "Bearer ghp_test"


# ─── Step 1d: Model Provider Selection in pipeline-setup SKILL.md ─────────

SKILL_MD = PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md"


def test_skill_md_contains_step_1d_header() -> None:
    """ADR-0054 pipeline-setup Step 1d: SKILL.md must contain a Step 1d header
    for Model Provider Selection so the skill surfaces provider config during install.
    """
    text = SKILL_MD.read_text(encoding="utf-8")
    assert "Step 1d" in text, (
        "SKILL.md must include a '### Step 1d' section for Model Provider Selection "
        "(required by ADR-0054 to configure model_provider at install time)."
    )


def test_skill_md_mentions_all_three_providers() -> None:
    """ADR-0054 pipeline-setup Step 1d: SKILL.md must name all three valid
    model_provider values so Bedrock and Vertex users can self-select during install.
    """
    text = SKILL_MD.read_text(encoding="utf-8")
    for provider in ("anthropic", "bedrock", "vertex"):
        assert provider in text, (
            f"SKILL.md must mention provider {provider!r} in Step 1d "
            "(ADR-0054 requires all three provider options to be offered)."
        )


def test_skill_md_contains_bedrock_env_var_guidance() -> None:
    """ADR-0054 pipeline-setup Step 1d: SKILL.md must document ANTHROPIC_AWS_REGION
    so Bedrock users know the required environment variable before running the pipeline.
    """
    text = SKILL_MD.read_text(encoding="utf-8")
    assert "ANTHROPIC_AWS_REGION" in text, (
        "SKILL.md must contain 'ANTHROPIC_AWS_REGION' guidance for Bedrock users "
        "(ADR-0054 Step 1d credential notes)."
    )


def test_skill_md_contains_vertex_env_var_guidance() -> None:
    """ADR-0054 pipeline-setup Step 1d: SKILL.md must document ANTHROPIC_VERTEX_PROJECT_ID
    so Vertex users know the required environment variable before running the pipeline.
    """
    text = SKILL_MD.read_text(encoding="utf-8")
    assert "ANTHROPIC_VERTEX_PROJECT_ID" in text, (
        "SKILL.md must contain 'ANTHROPIC_VERTEX_PROJECT_ID' guidance for Vertex users "
        "(ADR-0054 Step 1d credential notes)."
    )


def test_skill_md_contains_credentials_stay_in_env_note() -> None:
    """ADR-0054 pipeline-setup Step 1d: SKILL.md must contain a note that credentials
    stay in the Claude Code environment and must not be written to pipeline-config.json.
    """
    text = SKILL_MD.read_text(encoding="utf-8")
    assert "Credentials stay in your Claude Code environment" in text, (
        "SKILL.md must contain the 'Credentials stay in your Claude Code environment' "
        "note warning users not to put API keys in pipeline-config.json "
        "(ADR-0054 Step 1d security guidance)."
    )
