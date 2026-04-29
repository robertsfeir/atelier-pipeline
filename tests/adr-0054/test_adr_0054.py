"""Structural tests for ADR-0054 -- pipeline-side concerns only.

Multi-Provider LLM Abstraction (Brain) and Pipeline Provider Routing.

ADR-0054 had two halves:
  - Brain-side: llm-provider.mjs adapters, config.mjs backward compat,
    embedding dimension checks. These lived in `brain/lib/*` while the
    brain was bundled inside this plugin.
  - Pipeline-side: model_provider field in pipeline-config.json, Bedrock
    and Vertex model IDs in pipeline-models.md, and Step 1d in the
    pipeline-setup skill.

Per ADR-0055 Phase 3 the brain moved to the standalone mybrain plugin and
`brain/` was deleted from this repo. The brain-side behavioral tests now
live in mybrain; only the pipeline-side structural assertions remain here.
"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PIPELINE_CONFIG = PROJECT_ROOT / "source" / "shared" / "pipeline" / "pipeline-config.json"
PIPELINE_MODELS = PROJECT_ROOT / "source" / "shared" / "rules" / "pipeline-models.md"


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
