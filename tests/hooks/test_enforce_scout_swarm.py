"""Tests for enforce-scout-swarm.sh (PreToolUse hook on Agent).

Tests that the hook blocks invocations of cal, roz, and colby when the
required scout evidence block is absent from the prompt, and allows through
when the block is present or skip conditions apply.

Test IDs: T-SCOUT-001 through T-SCOUT-025
"""

import json
import subprocess

from conftest import (
    hide_jq_env,
    prepare_hook,
    run_hook,
    write_pipeline_status,
)


def _config_with_state_dir(tmp_path):
    """Write an enforcement-config.json pointing pipeline_state_dir at tmp_path/docs/pipeline."""
    (tmp_path / "enforcement-config.json").write_text(
        json.dumps({"pipeline_state_dir": str(tmp_path / "docs" / "pipeline")})
    )


def build_agent_prompt_input(subagent_type: str, prompt: str = "", agent_id: str | None = None) -> str:
    """Build a PreToolUse JSON for Agent tool with a prompt field."""
    d: dict = {
        "tool_name": "Agent",
        "tool_input": {
            "subagent_type": subagent_type,
            "prompt": prompt,
        },
    }
    if agent_id is not None:
        d["agent_id"] = agent_id
    return json.dumps(d, separators=(",", ":"))


# ── T-SCOUT-001: jq missing → exit 2 ───────────────────────────────────────

def test_T_SCOUT_002_non_agent_tool_passthrough(hook_env):
    _config_with_state_dir(hook_env)
    inp = json.dumps({"tool_name": "Write", "tool_input": {"file_path": "foo.py"}})
    r = run_hook("enforce-scout-swarm.sh", inp, hook_env)
    assert r.returncode == 0


# ── T-SCOUT-003: non-main-thread (agent_id set) → pass through ─────────────

def test_T_SCOUT_003_subagent_thread_passthrough(hook_env):
    _config_with_state_dir(hook_env)
    # No prompt needed — subagent thread bypasses all checks
    inp = build_agent_prompt_input("colby", "", agent_id="subagent-abc123")
    r = run_hook("enforce-scout-swarm.sh", inp, hook_env)
    assert r.returncode == 0


# ── T-SCOUT-004: non-target agent (e.g. agatha) → pass through ─────────────

def test_T_SCOUT_004_non_target_agent_passthrough(hook_env):
    _config_with_state_dir(hook_env)
    # agatha has no required block
    inp = build_agent_prompt_input("agatha", "no block here")
    r = run_hook("enforce-scout-swarm.sh", inp, hook_env)
    assert r.returncode == 0


# ── T-SCOUT-005: colby missing <colby-context> → blocked ───────────────────

def test_T_SCOUT_005_colby_missing_block_blocked(hook_env):
    write_pipeline_status(hook_env, '{"phase":"build","sizing":"medium"}')
    _config_with_state_dir(hook_env)
    inp = build_agent_prompt_input("colby", "Implement the feature as per the ADR.")
    r = run_hook("enforce-scout-swarm.sh", inp, hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout
    assert "colby-context" in r.stdout


# ── T-SCOUT-006: colby with <colby-context> → allowed ──────────────────────

def test_T_SCOUT_006_colby_with_block_allowed(hook_env):
    write_pipeline_status(hook_env, '{"phase":"build","sizing":"medium"}')
    _config_with_state_dir(hook_env)
    inp = build_agent_prompt_input(
        "colby",
        "<colby-context><existing-code>foo.py lines 1-120, entry point for feature</existing-code></colby-context>\nImplement the feature.",
    )
    r = run_hook("enforce-scout-swarm.sh", inp, hook_env)
    assert r.returncode == 0


# ── T-SCOUT-007: cal missing <research-brief> → blocked ────────────────────

def test_T_SCOUT_007_sarah_missing_block_blocked(hook_env):
    write_pipeline_status(hook_env, '{"phase":"design","sizing":"medium"}')
    _config_with_state_dir(hook_env)
    inp = build_agent_prompt_input("sarah", "Write an ADR for this feature.")
    r = run_hook("enforce-scout-swarm.sh", inp, hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout
    assert "research-brief" in r.stdout


# ── T-SCOUT-008: cal with <research-brief> → allowed ───────────────────────

def test_T_SCOUT_008_cal_with_block_allowed(hook_env):
    write_pipeline_status(hook_env, '{"phase":"design","sizing":"medium"}')
    _config_with_state_dir(hook_env)
    inp = build_agent_prompt_input(
        "sarah",
        "<research-brief><patterns>found pattern at line 42 of source/claude/hooks/enforce.sh</patterns></research-brief>\nWrite ADR.",
    )
    r = run_hook("enforce-scout-swarm.sh", inp, hook_env)
    assert r.returncode == 0


# ── T-SCOUT-009: roz missing both debug-evidence and qa-evidence → blocked ──

def test_T_SCOUT_012_colby_micro_skip(hook_env):
    """Micro pipeline skips colby enforcement — no block required."""
    write_pipeline_status(hook_env, '{"phase":"build","sizing":"micro"}')
    _config_with_state_dir(hook_env)
    # No <colby-context> but sizing=micro → should pass
    inp = build_agent_prompt_input("colby", "Implement the micro fix.")
    r = run_hook("enforce-scout-swarm.sh", inp, hook_env)
    assert r.returncode == 0


# ── T-SCOUT-013: cal skip when sizing=small ────────────────────────────────

def test_T_SCOUT_013_sarah_small_skip(hook_env):
    """Small pipeline skips sarah enforcement — no block required."""
    write_pipeline_status(hook_env, '{"phase":"design","sizing":"small"}')
    _config_with_state_dir(hook_env)
    # No <research-brief> but sizing=small → should pass
    inp = build_agent_prompt_input("sarah", "Write a quick ADR.")
    r = run_hook("enforce-scout-swarm.sh", inp, hook_env)
    assert r.returncode == 0


# ── T-SCOUT-014: roz skip when scoped_rerun=true ───────────────────────────

def test_T_SCOUT_015_fail_open_no_state_file(hook_env):
    """No pipeline-state.md → fail-open, no block enforcement."""
    _config_with_state_dir(hook_env)
    # No state file written; no block in prompt — should still pass (fail-open)
    inp = build_agent_prompt_input("colby", "Implement the feature.")
    r = run_hook("enforce-scout-swarm.sh", inp, hook_env)
    assert r.returncode == 0


# ── T-SCOUT-016: fail-open when prompt is empty ────────────────────────────

def test_T_SCOUT_016_fail_open_empty_prompt(hook_env):
    """Empty prompt → no block to check, fail-open."""
    write_pipeline_status(hook_env, '{"phase":"build","sizing":"medium"}')
    _config_with_state_dir(hook_env)
    inp = build_agent_prompt_input("colby", "")
    r = run_hook("enforce-scout-swarm.sh", inp, hook_env)
    assert r.returncode == 0


# ── T-SCOUT-017: colby with micro but block present → allowed ──────────────

def test_T_SCOUT_017_colby_micro_with_block_allowed(hook_env):
    """Micro pipeline with block present: skip condition plus block — both pass."""
    write_pipeline_status(hook_env, '{"phase":"build","sizing":"micro"}')
    _config_with_state_dir(hook_env)
    inp = build_agent_prompt_input(
        "colby",
        "<colby-context>context here: feature flag enabled, see source/shared/agents/colby.md</colby-context>",
    )
    r = run_hook("enforce-scout-swarm.sh", inp, hook_env)
    assert r.returncode == 0


# ── T-SCOUT-018: cal with medium and block → allowed ───────────────────────

def test_T_SCOUT_018_cal_medium_with_block_allowed(hook_env):
    """Medium pipeline requires research-brief; it's present → allowed."""
    write_pipeline_status(hook_env, '{"phase":"design","sizing":"medium"}')
    _config_with_state_dir(hook_env)
    inp = build_agent_prompt_input(
        "sarah",
        "<research-brief>Pattern analysis complete. Found 3 matching hooks in source/claude/hooks/.</research-brief>",
    )
    r = run_hook("enforce-scout-swarm.sh", inp, hook_env)
    assert r.returncode == 0


# ── T-SCOUT-019: cal with medium and no block → blocked ────────────────────

def test_T_SCOUT_019_sarah_medium_missing_block_blocked(hook_env):
    """Medium pipeline requires research-brief; it's absent → blocked."""
    write_pipeline_status(hook_env, '{"phase":"design","sizing":"medium"}')
    _config_with_state_dir(hook_env)
    inp = build_agent_prompt_input("sarah", "Just go ahead and architect this.")
    r = run_hook("enforce-scout-swarm.sh", inp, hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


# ── T-SCOUT-020: colby with large and block → allowed ──────────────────────

def test_T_SCOUT_020_colby_large_with_block_allowed(hook_env):
    """Large pipeline requires colby-context; it's present → allowed."""
    write_pipeline_status(hook_env, '{"phase":"build","sizing":"large"}')
    _config_with_state_dir(hook_env)
    inp = build_agent_prompt_input(
        "colby",
        "<colby-context><existing-code>main.py is the entry point, 340 lines</existing-code></colby-context>",
    )
    r = run_hook("enforce-scout-swarm.sh", inp, hook_env)
    assert r.returncode == 0


# ── T-SCOUT-021: colby with large and no block → blocked ───────────────────

def test_T_SCOUT_021_colby_large_missing_block_blocked(hook_env):
    """Large pipeline requires colby-context; it's absent → blocked."""
    write_pipeline_status(hook_env, '{"phase":"build","sizing":"large"}')
    _config_with_state_dir(hook_env)
    inp = build_agent_prompt_input("colby", "Build the feature per ADR-0034.")
    r = run_hook("enforce-scout-swarm.sh", inp, hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout
    assert "colby-context" in r.stdout


# ── T-SCOUT-022: roz with scoped_rerun=false and no block → blocked ─────────

def test_T_SCOUT_024_setup_mode_bypass(hook_env):
    """ATELIER_SETUP_MODE=1 bypasses all checks."""
    _config_with_state_dir(hook_env)
    import os
    env = os.environ.copy()
    env["ATELIER_SETUP_MODE"] = "1"
    inp = build_agent_prompt_input("colby", "No context block here.")
    hook_path = prepare_hook("enforce-scout-swarm.sh", hook_env)
    r = subprocess.run(
        ["bash", str(hook_path)],
        input=inp,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        timeout=30,
    )
    assert r.returncode == 0


# ── T-SCOUT-025: roz with both qa-evidence and debug-evidence → allowed ─────

def test_T_SCOUT_026_sarah_empty_research_brief_blocked(hook_env):
    """Empty <research-brief></research-brief> block is blocked — empty-block bypass fix."""
    write_pipeline_status(hook_env, '{"phase":"design","sizing":"medium"}')
    _config_with_state_dir(hook_env)
    inp = build_agent_prompt_input("sarah", "<research-brief></research-brief>\nWrite ADR.")
    r = run_hook("enforce-scout-swarm.sh", inp, hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout
    assert "research-brief" in r.stdout


# ── T-SCOUT-027: cal <research-brief> with 60+ chars of content → allowed ──

def test_T_SCOUT_027_cal_research_brief_sufficient_content_allowed(hook_env):
    """<research-brief> block with 60+ chars of real content passes the content check."""
    write_pipeline_status(hook_env, '{"phase":"design","sizing":"medium"}')
    _config_with_state_dir(hook_env)
    # Content is 73 chars: well over the 50-char minimum
    content = "Found enforce-scout-swarm.sh at source/claude/hooks/ — 3 related patterns"
    inp = build_agent_prompt_input(
        "sarah",
        f"<research-brief>{content}</research-brief>\nWrite ADR.",
    )
    r = run_hook("enforce-scout-swarm.sh", inp, hook_env)
    assert r.returncode == 0


# ═══════════════════════════════════════════════════════════════════════
# ADR-0033 Step 3 (M3): Roz content validation in <debug-evidence>/<qa-evidence>
# ═══════════════════════════════════════════════════════════════════════
#
# The existing T-SCOUT-009 covers the "no tag at all" case. T-0033-009 through
# -013 add content-validation coverage symmetric to the cal/colby branches:
# empty tag, whitespace-only tag, too-short content (< 50 chars), either-or
# preservation, and the happy path with a well-formed 200-char block.
#
# Colby MUST NOT modify these assertions.


# ── T-0033-009: empty <debug-evidence></debug-evidence> → blocked ──────────
