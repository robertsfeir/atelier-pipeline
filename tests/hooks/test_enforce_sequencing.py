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


# ═══════════════════════════════════════════════════════════════════════
# Gate 5: Robert review
# ═══════════════════════════════════════════════════════════════════════


def test_T_GATE5_001_robert_missing_medium(hook_env):
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
