"""Tests for enforce-pipeline-activation.sh (PreToolUse hook on Agent)."""

import json
import subprocess

import pytest

from conftest import (
    build_agent_input,
    build_tool_input,
    hide_jq_env,
    prepare_hook,
    run_hook,
    write_pipeline_freeform,
    write_pipeline_status,
)


def _config_with_state_dir(tmp_path):
    (tmp_path / "enforcement-config.json").write_text(
        json.dumps({"pipeline_state_dir": str(tmp_path / "docs" / "pipeline")})
    )


def test_colby_allowed_active_build(hook_env):
    write_pipeline_status(hook_env, '{"phase":"build","roz_qa":""}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("colby"), hook_env)
    assert r.returncode == 0


def test_ellis_allowed_active_review(hook_env):
    write_pipeline_status(hook_env, '{"phase":"review","roz_qa":"PASS"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


def test_colby_blocked_no_state_file(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").unlink(missing_ok=True)
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("colby"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout
    assert "colby" in r.stdout
    assert "/pipeline" in r.stdout


# RETIRED: Ellis removed from enforce-pipeline-activation.sh (ADR context:
# Ellis outside pipeline now handled by enforce-sequencing.sh Gate 1, which
# allows Ellis when there is no state file, no marker, or an idle/complete/none
# phase — covering infrastructure, doc-only, and setup/release-tag commits.
# Blocking Ellis here would make that nuanced gate dead letter and prevent
# release tagging outside a pipeline). This behavior no longer exists in this hook.
@pytest.mark.skip(reason="Retired: Ellis removed from this hook — enforce-sequencing.sh Gate 1 handles outside-pipeline Ellis")
def test_ellis_blocked_no_marker(hook_env):
    write_pipeline_freeform(hook_env, "Pipeline is running. Phase: review.")
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout
    assert "ellis" in r.stdout


def test_colby_blocked_phase_idle(hook_env):
    write_pipeline_status(hook_env, '{"phase":"idle","roz_qa":""}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("colby"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout
    assert "colby" in r.stdout


# RETIRED: Ellis removed from enforce-pipeline-activation.sh (ADR context:
# Ellis outside pipeline now handled by enforce-sequencing.sh Gate 1, which
# allows Ellis when there is no state file, no marker, or an idle/complete/none
# phase — covering infrastructure, doc-only, and setup/release-tag commits.
# Blocking Ellis here would make that nuanced gate dead letter and prevent
# release tagging outside a pipeline). This behavior no longer exists in this hook.
@pytest.mark.skip(reason="Retired: Ellis removed from this hook — enforce-sequencing.sh Gate 1 handles outside-pipeline Ellis")
def test_ellis_blocked_phase_complete(hook_env):
    write_pipeline_status(hook_env, '{"phase":"complete","roz_qa":"PASS"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout
    assert "ellis" in r.stdout


def test_colby_blocked_phase_none(hook_env):
    write_pipeline_status(hook_env, '{"phase":"none","roz_qa":""}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("colby"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_colby_blocked_phase_COMPLETE_uppercase(hook_env):
    write_pipeline_status(hook_env, '{"phase":"COMPLETE","roz_qa":"PASS"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("colby"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_roz_allowed_no_pipeline(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").unlink(missing_ok=True)
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("roz"), hook_env)
    assert r.returncode == 0


def test_cal_allowed_no_pipeline(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").unlink(missing_ok=True)
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("cal"), hook_env)
    assert r.returncode == 0


def test_agatha_allowed_no_pipeline(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").unlink(missing_ok=True)
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("agatha"), hook_env)
    assert r.returncode == 0


def test_colby_subagent_context_allowed(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").unlink(missing_ok=True)
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("colby", "subagent-123"), hook_env)
    assert r.returncode == 0


def test_config_missing_exits_0(hook_env):
    (hook_env / "enforcement-config.json").unlink()
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("colby"), hook_env)
    assert r.returncode == 0


def test_jq_missing_exits_2(hook_env):
    env = hide_jq_env(hook_env)
    hook_path = prepare_hook("enforce-pipeline-activation.sh", hook_env)
    r = subprocess.run(
        ["bash", str(hook_path)], input=build_agent_input("colby"),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, timeout=30,
    )
    assert r.returncode == 2
    assert "jq" in r.stdout or "jq" in r.stderr


def test_colby_blocked_malformed_json(hook_env):
    state_file = hook_env / "docs" / "pipeline" / "pipeline-state.md"
    state_file.write_text("# Pipeline State\n\n<!-- PIPELINE_STATUS: {phase: broken, not json} -->\n")
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("colby"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_colby_allowed_architecture_phase(hook_env):
    write_pipeline_status(hook_env, '{"phase":"architecture","roz_qa":""}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("colby"), hook_env)
    assert r.returncode == 0


def test_ellis_allowed_implement_phase(hook_env):
    write_pipeline_status(hook_env, '{"phase":"implement","roz_qa":"PASS","telemetry_captured":"true"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


def test_non_agent_tool_ignored(hook_env):
    r = run_hook("enforce-pipeline-activation.sh", build_tool_input("Write", "src/test.js", "colby"), hook_env)
    assert r.returncode == 0


def test_block_message_names_colby(hook_env):
    write_pipeline_status(hook_env, '{"phase":"complete","roz_qa":"PASS"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("colby"), hook_env)
    assert r.returncode == 2
    assert "colby" in r.stdout


# RETIRED: Ellis removed from enforce-pipeline-activation.sh (ADR context:
# Ellis outside pipeline now handled by enforce-sequencing.sh Gate 1, which
# allows Ellis when there is no state file, no marker, or an idle/complete/none
# phase — covering infrastructure, doc-only, and setup/release-tag commits.
# Blocking Ellis here would make that nuanced gate dead letter and prevent
# release tagging outside a pipeline). This behavior no longer exists in this hook.
@pytest.mark.skip(reason="Retired: Ellis removed from this hook — enforce-sequencing.sh Gate 1 handles outside-pipeline Ellis")
def test_block_message_names_ellis(hook_env):
    write_pipeline_status(hook_env, '{"phase":"idle","roz_qa":""}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 2
    assert "ellis" in r.stdout


def test_colby_blocked_phase_Idle_mixed_case(hook_env):
    write_pipeline_status(hook_env, '{"phase":"Idle","roz_qa":""}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("colby"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


# --- New tests documenting Ellis allow-through behavior (added after architectural change) ---

def test_ellis_allowed_no_marker(hook_env):
    # Ellis removed from enforce-pipeline-activation.sh — handled by enforce-sequencing.sh Gate 1.
    # This hook now passes Ellis through unconditionally; sequencing.sh enforces roz_qa.
    write_pipeline_freeform(hook_env, "Pipeline is running. Phase: review.")
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


def test_ellis_allowed_phase_complete(hook_env):
    # Ellis removed from enforce-pipeline-activation.sh — handled by enforce-sequencing.sh Gate 1.
    write_pipeline_status(hook_env, '{"phase":"complete","roz_qa":"PASS"}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0


def test_ellis_allowed_phase_idle(hook_env):
    # Ellis removed from enforce-pipeline-activation.sh — handled by enforce-sequencing.sh Gate 1.
    write_pipeline_status(hook_env, '{"phase":"idle","roz_qa":""}')
    _config_with_state_dir(hook_env)
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0
