"""Tests for enforce-sequencing.sh (PreToolUse hook on Agent).

Covers T-0003-030, T-0003-042 through T-0003-048, T-0003-057,
T-0013-051 through T-0013-059, T-GATE3-001 through T-GATE3-004,
T-GATE4-001 through T-GATE4-004, T-GATE5-001 through T-GATE5-005.
"""

import json
import subprocess

from conftest import (
    build_agent_input,
    hide_jq_env,
    prepare_hook,
    run_hook,
    write_pipeline_freeform,
    write_pipeline_status,
)


def _config_with_state_dir(tmp_path):
    """Write a config pointing pipeline_state_dir to tmp_path/docs/pipeline."""
    (tmp_path / "enforcement-config.json").write_text(
        json.dumps({"pipeline_state_dir": str(tmp_path / "docs" / "pipeline")})
    )


# ── T-0003-030: jq missing ──────────────────────────────────────────────

def test_T_0003_030_jq_missing(hook_env):
    env = hide_jq_env(hook_env)
    inp = build_agent_input("ellis")
    hook_path = prepare_hook("enforce-sequencing.sh", hook_env)
    r = subprocess.run(["bash", str(hook_path)], input=inp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, timeout=30)
    assert r.returncode == 2
    assert "jq" in r.stdout or "jq" in r.stderr


# ── T-0003-042: Ellis with roz_qa=PASS ──────────────────────────────────

def test_T_0003_042_ellis_roz_qa_pass(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"PASS","phase":"review"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


# ── T-0003-043: Ellis with roz_qa=FAIL ──────────────────────────────────

def test_T_0003_043_ellis_roz_qa_fail(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"FAIL","phase":"review"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


# ── T-0003-044: no PIPELINE_STATUS marker -- fail-open ──────────────────

def test_T_0003_044_no_marker_fail_open(hook_env):
    write_pipeline_freeform(hook_env, "Pipeline is running. Phase: review.")
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


# ── T-0003-045: malformed JSON -- fail-open ─────────────────────────────

def test_T_0003_045_malformed_json_fail_open(hook_env):
    state_file = hook_env / "docs" / "pipeline" / "pipeline-state.md"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text("# Pipeline State\n\n<!-- PIPELINE_STATUS: {roz_qa: PASS, broken json} -->\n")
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


# ── T-0003-046: Agatha during build phase blocked ───────────────────────

def test_T_0003_046_agatha_build_blocked(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"","phase":"build"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("agatha"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout
    assert "Agatha" in r.stdout


# ── T-0003-047: Agatha during review phase allowed ──────────────────────

def test_T_0003_047_agatha_review_allowed(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"PASS","phase":"review"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("agatha"), hook_env)
    assert r.returncode == 0


# ── T-0003-048: non-main-thread always exits 0 ──────────────────────────

def test_T_0003_048_non_main_thread(hook_env):
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis", "subagent-123"), hook_env)
    assert r.returncode == 0


# ── T-0003-057: free-form text fails open ────────────────────────────────

def test_T_0003_057_freeform_text_fails_open(hook_env):
    write_pipeline_freeform(hook_env, "roz passed QA with flying colors. Everything looks great.")
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


# ═══════════════════════════════════════════════════════════════════════
# ADR-0013 CI Watch
# ═══════════════════════════════════════════════════════════════════════


def test_T_0013_051_ellis_ci_verified(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"CI_VERIFIED","phase":"review","ci_watch_active":true,"ci_watch_retry_count":1}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


def test_T_0013_052_ellis_ci_watch_empty_roz_qa(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"","phase":"review","ci_watch_active":true,"ci_watch_retry_count":0}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_T_0013_053_ellis_ci_watch_inactive_fail(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"FAIL","phase":"build","ci_watch_active":false}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_T_0013_054_ellis_ci_watch_inactive_pass(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"PASS","phase":"review","ci_watch_active":false}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


def test_T_0013_055_regression_gate1(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"","phase":"build"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_two_hook_chain_ellis_active_phase_no_roz_qa(hook_env):
    """Two-hook chain: enforce-pipeline-activation.sh passes Ellis (no phase check for Ellis),
    but enforce-sequencing.sh Gate 1 still blocks Ellis when roz_qa is empty.

    Confirms that removing Ellis from enforce-pipeline-activation.sh did not create a gap —
    enforce-sequencing.sh Gate 1 is the authoritative guard for roz_qa enforcement.
    """
    write_pipeline_status(hook_env, '{"phase":"build","roz_qa":"","sizing":"small"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_T_0013_056_regression_gate2_agatha(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"","phase":"build","ci_watch_active":true}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("agatha"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout
    assert "Agatha" in r.stdout


def test_T_0013_057_extended_json_parses(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"PASS","phase":"review","ci_watch_active":false,"ci_watch_retry_count":0,"ci_watch_commit_sha":"abc123"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


def test_T_0013_058_malformed_json_ci_watch_fail_open(hook_env):
    state_file = hook_env / "docs" / "pipeline" / "pipeline-state.md"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text('# Pipeline State\n\n<!-- PIPELINE_STATUS: {"roz_qa":"CI_VERIFIED","ci_watch_active":true, broken -->\n')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


def test_T_0013_059_ci_verified_requires_active(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"CI_VERIFIED","phase":"review","ci_watch_active":false}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_gate1_phase_none_ellis_allowed(hook_env):
    """Gate 1: Ellis is allowed when phase=none (no active pipeline).

    phase:none means Ellis is running outside a pipeline context —
    enforce-sequencing.sh should not block it on roz_qa grounds.
    """
    write_pipeline_status(hook_env, '{"phase":"none","roz_qa":""}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


# ═══════════════════════════════════════════════════════════════════════
# Gate 3: Telemetry capture
# ═══════════════════════════════════════════════════════════════════════


def test_T_GATE3_001_telemetry_missing(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"PASS","phase":"review","sizing":"medium"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_T_GATE3_002_telemetry_captured(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"PASS","phase":"review","sizing":"medium","telemetry_captured":"true","poirot_reviewed":"true","robert_reviewed":"true"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


def test_T_GATE3_003_micro_no_telemetry(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"PASS","phase":"review","sizing":"micro"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


def test_T_GATE3_004_ci_watch_no_telemetry(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"CI_VERIFIED","phase":"review","sizing":"medium","ci_watch_active":"true"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


def test_gate3_phase_none_no_telemetry_required(hook_env):
    """Gate 3: Telemetry not required when phase=none, even with sizing=medium.

    phase:none means no active pipeline, so telemetry capture is not applicable.
    """
    write_pipeline_status(hook_env, '{"roz_qa":"PASS","phase":"none","sizing":"medium"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


# ═══════════════════════════════════════════════════════════════════════
# Gate 4: Poirot review
# ═══════════════════════════════════════════════════════════════════════


def test_T_GATE4_001_poirot_missing(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"PASS","phase":"build","sizing":"small","telemetry_captured":"true"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout
    assert "Poirot" in r.stdout


def test_T_GATE4_002_poirot_reviewed(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"PASS","phase":"build","sizing":"small","telemetry_captured":"true","poirot_reviewed":"true"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


def test_T_GATE4_003_micro_no_poirot(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"PASS","phase":"review","sizing":"micro"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


def test_T_GATE4_004_ci_watch_no_poirot(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"CI_VERIFIED","phase":"review","sizing":"small","ci_watch_active":"true"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


def test_gate4_phase_none_no_poirot_required(hook_env):
    """Gate 4: Poirot not required when phase=none, even with sizing=small.

    phase:none means no active pipeline, so Poirot review is not applicable.
    """
    write_pipeline_status(hook_env, '{"roz_qa":"PASS","phase":"none","sizing":"small"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


# ═══════════════════════════════════════════════════════════════════════
# Gate 5: Robert review
# ═══════════════════════════════════════════════════════════════════════


def test_T_GATE5_001_robert_missing_medium(hook_env):
    # Gate 5 semantic: spec exists in docs/product/ AND Robert hasn't reviewed → BLOCK.
    # (Absent docs/product/ triggers the Gate 5 amendment fail-open path — tested
    # separately in test_gate5_no_product_specs_ellis_allowed.)
    product_dir = hook_env / "docs" / "product"
    product_dir.mkdir(parents=True, exist_ok=True)
    (product_dir / "feature-x.md").write_text("# Feature X\n\nSpec body.\n")

    write_pipeline_status(hook_env, '{"roz_qa":"PASS","phase":"review","sizing":"medium","telemetry_captured":"true","poirot_reviewed":"true"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout
    assert "Robert" in r.stdout


def test_T_GATE5_002_robert_reviewed_medium(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"PASS","phase":"review","sizing":"medium","telemetry_captured":"true","poirot_reviewed":"true","robert_reviewed":"true"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


def test_T_GATE5_003_small_exempt(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"PASS","phase":"review","sizing":"small","telemetry_captured":"true","poirot_reviewed":"true"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


def test_T_GATE5_004_build_phase_exempt(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"PASS","phase":"build","sizing":"medium","telemetry_captured":"true","poirot_reviewed":"true"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


def test_T_GATE5_005_large_with_robert(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"PASS","phase":"review","sizing":"large","telemetry_captured":"true","poirot_reviewed":"true","robert_reviewed":"true"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


# ═══════════════════════════════════════════════════════════════════════
# Gate 0b: Investigator worktree_path enforcement
# ═══════════════════════════════════════════════════════════════════════
# When subagent_type=investigator and pipeline state carries a non-null
# worktree_path, the invocation prompt must reference that worktree_path
# string. Otherwise BLOCK — the investigator would read files from the
# wrong location.


def _build_investigator_input(prompt: str) -> str:
    """Build an Agent invocation for investigator with a prompt string.

    build_agent_input() does not populate tool_input.prompt; Gate 0b needs
    the prompt body to perform substring matching, so we construct the JSON
    inline here with the same shape the hook reads via .tool_input.prompt.
    """
    return json.dumps(
        {"tool_name": "Agent", "tool_input": {"subagent_type": "investigator", "prompt": prompt}},
        separators=(",", ":"),
    )


def test_gate0b_investigator_missing_worktree_path_blocked(hook_env):
    """Gate 0b: investigator invoked without worktree_path in prompt is BLOCKED
    when pipeline state carries a non-null worktree_path."""
    write_pipeline_status(
        hook_env,
        '{"phase":"review","roz_qa":"PASS","worktree_path":"/Users/x/projects/atelier-pipeline-ac008bc4"}',
    )
    _config_with_state_dir(hook_env)
    # Prompt references a generic investigation task but omits the worktree path
    prompt = "Investigate the failing enforcement hook. Look at source/claude/hooks/enforce-sequencing.sh."
    r = run_hook("enforce-sequencing.sh", _build_investigator_input(prompt), hook_env)
    assert r.returncode == 2, f"Expected BLOCK (2), got {r.returncode}. Output: {r.stdout}"
    assert "BLOCKED" in r.stdout
    assert "worktree" in r.stdout.lower()


def test_gate0b_investigator_with_worktree_path_allowed(hook_env):
    """Gate 0b: investigator invoked with worktree_path embedded in prompt is
    ALLOWED — the prompt correctly directs the investigator to the worktree."""
    worktree = "/Users/x/projects/atelier-pipeline-ac008bc4"
    write_pipeline_status(
        hook_env,
        f'{{"phase":"review","roz_qa":"PASS","worktree_path":"{worktree}"}}',
    )
    _config_with_state_dir(hook_env)
    prompt = f"Investigate the failing enforcement hook in worktree {worktree}. Start at source/claude/hooks/enforce-sequencing.sh."
    r = run_hook("enforce-sequencing.sh", _build_investigator_input(prompt), hook_env)
    assert r.returncode == 0, f"Expected ALLOW (0), got {r.returncode}. Output: {r.stdout}"


def test_gate0b_investigator_basename_only_blocked(hook_env):
    """Gate 0b: investigator invoked with only the worktree *basename* (not the
    full absolute path) is BLOCKED. The substring match must require the full
    worktree_path — a bare basename like 'atelier-pipeline-ac008bc4' could
    match any sibling directory or unrelated token and does not correctly
    direct the investigator to the worktree."""
    worktree = "/Users/x/projects/atelier-pipeline-ac008bc4"
    write_pipeline_status(
        hook_env,
        f'{{"phase":"review","roz_qa":"PASS","worktree_path":"{worktree}"}}',
    )
    _config_with_state_dir(hook_env)
    # Prompt mentions only the basename, not the full absolute worktree path.
    prompt = "Investigate in atelier-pipeline-ac008bc4 the failing enforcement hook."
    r = run_hook("enforce-sequencing.sh", _build_investigator_input(prompt), hook_env)
    assert r.returncode == 2, f"Expected BLOCK (2), got {r.returncode}. Output: {r.stdout}"
    assert "BLOCKED" in r.stdout
    assert "worktree" in r.stdout.lower()


# ═══════════════════════════════════════════════════════════════════════
# Gate 5 amendment: skip Robert requirement when docs/product/ has no specs
# ═══════════════════════════════════════════════════════════════════════
# Amendment: if the product specs directory contains no .md files, the
# Robert-reviewed requirement is vestigial (there is no spec to accept).
# Ellis should be allowed through on medium/large sizing in review phase
# even when robert_reviewed is false, provided docs/product/ is empty of
# markdown specs. If any .md specs exist, the original block still applies.


def test_gate5_no_product_specs_ellis_allowed(hook_env):
    """Gate 5 amendment: when docs/product/ exists but contains no .md specs,
    Robert review is not required — Ellis passes on medium sizing even when
    robert_reviewed is false."""
    # Create the product specs directory but leave it empty of .md files.
    product_dir = hook_env / "docs" / "product"
    product_dir.mkdir(parents=True, exist_ok=True)
    # A non-.md file should not satisfy "specs exist" either.
    (product_dir / ".gitkeep").write_text("")

    write_pipeline_status(
        hook_env,
        '{"roz_qa":"PASS","phase":"review","sizing":"medium","telemetry_captured":"true","poirot_reviewed":"true"}',
    )
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0, f"Expected ALLOW (0), got {r.returncode}. Output: {r.stdout}"


def test_gate5_product_specs_exist_ellis_still_blocked(hook_env):
    """Gate 5 amendment regression: when docs/product/ contains .md specs,
    the Robert-review block still applies — the amendment does not open a
    hole when specs are present."""
    product_dir = hook_env / "docs" / "product"
    product_dir.mkdir(parents=True, exist_ok=True)
    (product_dir / "feature-x.md").write_text("# Feature X\n\nSpec body.\n")

    write_pipeline_status(
        hook_env,
        '{"roz_qa":"PASS","phase":"review","sizing":"medium","telemetry_captured":"true","poirot_reviewed":"true"}',
    )
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 2, f"Expected BLOCK (2), got {r.returncode}. Output: {r.stdout}"
    assert "BLOCKED" in r.stdout
    assert "Robert" in r.stdout


# ═══════════════════════════════════════════════════════════════════════
# Gate 0b regression: investigator fail-open when worktree_path absent/null
# ═══════════════════════════════════════════════════════════════════════
# When pipeline state has no worktree_path (absent or null), Gate 0b must
# fail open — the investigator has not been dispatched to a worktree, so
# the invocation prompt is not required to reference one. Blocking here
# would break investigator invocations in non-worktree pipelines.


def test_gate0b_investigator_no_worktree_path_fail_open(hook_env):
    """Gate 0b regression lock: investigator is ALLOWED when pipeline state
    carries no worktree_path field. The prompt does not need to reference a
    worktree path that does not exist."""
    write_pipeline_status(
        hook_env,
        '{"phase":"review","roz_qa":"PASS"}',
    )
    _config_with_state_dir(hook_env)
    prompt = "Investigate the failing enforcement hook. Look at source/claude/hooks/enforce-sequencing.sh."
    r = run_hook("enforce-sequencing.sh", _build_investigator_input(prompt), hook_env)
    assert r.returncode == 0, f"Expected ALLOW (0), got {r.returncode}. Output: {r.stdout}"
