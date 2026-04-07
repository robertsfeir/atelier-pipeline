"""ADR-0022 Phase 2: Wave-boundary compaction advisory hook.
Step 2h. Tests T-0022-170 through T-0022-191."""

import subprocess

import pytest

from conftest import (
    PROJECT_ROOT,
    CLAUDE_DIR,
    SHARED_DIR,
    SOURCE_DIR,
    build_subagent_stop_input,
    hide_jq_env,
    prepare_compact_advisory_hook,
    run_compact_advisory,
    write_pipeline_status,
)


def test_T_0022_170_exists_executable():
    hook = CLAUDE_DIR / "hooks" / "prompt-compact-advisory.sh"
    assert hook.exists()
    assert hook.stat().st_mode & 0o111


def test_T_0022_171_build_phase(hook_env):
    write_pipeline_status(hook_env, '{"phase":"build"}')
    inp = build_subagent_stop_input("ellis", "agent-123", "session-xyz", "Committed wave 2")
    r = run_compact_advisory(inp, hook_env)
    assert r.returncode == 0
    assert "WAVE BOUNDARY" in r.stdout
    assert "/compact" in r.stdout


def test_T_0022_172_implement_phase(hook_env):
    write_pipeline_status(hook_env, '{"phase":"implement"}')
    inp = build_subagent_stop_input("ellis", "agent-123", "session-xyz", "Committed wave 2")
    r = run_compact_advisory(inp, hook_env)
    assert r.returncode == 0
    assert "WAVE BOUNDARY" in r.stdout
    assert "/compact" in r.stdout


def test_T_0022_173_review_phase_silent(hook_env):
    write_pipeline_status(hook_env, '{"phase":"review"}')
    inp = build_subagent_stop_input("ellis", "agent-123", "session-xyz", "Final commit")
    r = run_compact_advisory(inp, hook_env)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_T_0022_174_complete_phase_silent(hook_env):
    write_pipeline_status(hook_env, '{"phase":"complete"}')
    inp = build_subagent_stop_input("ellis", "agent-123", "session-xyz", "Pipeline complete")
    r = run_compact_advisory(inp, hook_env)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_T_0022_175_idle_phase_silent(hook_env):
    write_pipeline_status(hook_env, '{"phase":"idle"}')
    inp = build_subagent_stop_input("ellis", "agent-123", "session-xyz", "Done")
    r = run_compact_advisory(inp, hook_env)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_T_0022_176_missing_state_file(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").unlink(missing_ok=True)
    inp = build_subagent_stop_input("ellis", "agent-123", "session-xyz", "Done")
    r = run_compact_advisory(inp, hook_env)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_T_0022_177_no_marker(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").write_text("# Pipeline State\n\nNo pipeline active.\n")
    inp = build_subagent_stop_input("ellis", "agent-123", "session-xyz", "Done")
    r = run_compact_advisory(inp, hook_env)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_T_0022_178_always_exits_0(hook_env):
    inp = build_subagent_stop_input("ellis", "agent-123", "session-xyz", "Done")

    # Advisory
    write_pipeline_status(hook_env, '{"phase":"build"}')
    r = run_compact_advisory(inp, hook_env)
    assert r.returncode == 0

    # Silent
    write_pipeline_status(hook_env, '{"phase":"review"}')
    r = run_compact_advisory(inp, hook_env)
    assert r.returncode == 0

    # Missing
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").unlink()
    r = run_compact_advisory(inp, hook_env)
    assert r.returncode == 0

    # Empty stdin
    hook_path = prepare_compact_advisory_hook(hook_env)
    import os
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(hook_env)
    r = subprocess.run(["bash", str(hook_path)], input="", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, timeout=30)
    assert r.returncode == 0

    # jq missing
    write_pipeline_status(hook_env, '{"phase":"build"}')
    env2 = hide_jq_env(hook_env)
    env2["CLAUDE_PROJECT_DIR"] = str(hook_env)
    r = subprocess.run(["bash", str(hook_path)], input=inp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env2, timeout=30)
    assert r.returncode == 0


def test_T_0022_179_empty_stdin(hook_env):
    write_pipeline_status(hook_env, '{"phase":"build"}')
    hook_path = prepare_compact_advisory_hook(hook_env)
    import os
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(hook_env)
    r = subprocess.run(["bash", str(hook_path)], input="", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, timeout=30)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_T_0022_180_jq_missing(hook_env):
    write_pipeline_status(hook_env, '{"phase":"build"}')
    env = hide_jq_env(hook_env)
    env["CLAUDE_PROJECT_DIR"] = str(hook_env)
    hook_path = prepare_compact_advisory_hook(hook_env)
    inp = build_subagent_stop_input("ellis", "agent-123", "session-xyz", "Done")
    r = subprocess.run(["bash", str(hook_path)], input=inp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, timeout=30)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_T_0022_181_not_ellis(hook_env):
    write_pipeline_status(hook_env, '{"phase":"build"}')
    inp = build_subagent_stop_input("colby", "agent-456", "session-xyz", "Unit done")
    r = run_compact_advisory(inp, hook_env)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_T_0022_182_under_35_lines():
    hook = CLAUDE_DIR / "hooks" / "prompt-compact-advisory.sh"
    assert len(hook.read_text().splitlines()) <= 35


def test_T_0022_183_no_file_writes():
    text = (CLAUDE_DIR / "hooks" / "prompt-compact-advisory.sh").read_text()
    import re
    assert not re.search(r'(>>?\s+["/]|tee\s)', text)


def test_T_0022_184_no_brain_tests_subagents():
    text = (CLAUDE_DIR / "hooks" / "prompt-compact-advisory.sh").read_text()
    assert "agent_capture" not in text
    assert "agent_search" not in text
    assert "bats" not in text
    assert "npm test" not in text
    assert "pytest" not in text
    assert "vitest" not in text
    assert '"Agent"' not in text


def test_T_0022_185_skill_md_has_hook():
    skill = (PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md").read_text()
    assert "prompt-compact-advisory.sh" in skill
    assert "source/claude/hooks/prompt-compact-advisory.sh" in skill
    assert ".claude/hooks/prompt-compact-advisory.sh" in skill


def test_T_0022_186_skill_md_settings():
    # prompt-compact-advisory.sh is installed via the file map table, not via settings JSON.
    # The hook itself filters to ellis internally (reads agent_type).
    import re
    skill = (PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md").read_text()
    assert "prompt-compact-advisory" in skill
    # Verify it is described in the hook file map as a SubagentStop hook
    assert re.search(r"prompt-compact-advisory.*SubagentStop|SubagentStop.*prompt-compact-advisory", skill)


def test_T_0022_187_pipeline_operations():
    ops_file = SHARED_DIR / "references" / "pipeline-operations.md"
    if not ops_file.exists():
        ops_file = SOURCE_DIR / "references" / "pipeline-operations.md"
    text = ops_file.read_text()
    assert "prompt-compact-advisory" in text
    import re
    assert re.search(r"wave.boundary|wave boundary", text, re.IGNORECASE)


def test_T_0022_188_existing_hooks():
    skill = (PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md").read_text()
    for hook in ["session-hydrate.sh", "log-agent-stop.sh", "prompt-brain-capture.sh", "warn-brain-capture.sh"]:
        assert hook in skill


def test_T_0022_189_user_decision_language(hook_env):
    write_pipeline_status(hook_env, '{"phase":"build"}')
    inp = build_subagent_stop_input("ellis", "agent-123", "session-xyz", "Done")
    r = run_compact_advisory(inp, hook_env)
    assert r.returncode == 0
    has_language = any([
        "user" in r.stdout and "decision" in r.stdout,
        "Do not auto-compact" in r.stdout,
        "do not auto-compact" in r.stdout,
        "user's decision" in r.stdout,
    ])
    assert has_language


def test_T_0022_190_project_dir_fallback():
    text = (CLAUDE_DIR / "hooks" / "prompt-compact-advisory.sh").read_text()
    assert "CLAUDE_PROJECT_DIR" in text
    assert "CURSOR_PROJECT_DIR" in text


def test_T_0022_191_unrecognized_phase(hook_env):
    write_pipeline_status(hook_env, '{"phase":"unknown"}')
    inp = build_subagent_stop_input("ellis", "agent-123", "session-xyz", "Done")
    r = run_compact_advisory(inp, hook_env)
    assert r.returncode == 0
    assert r.stdout.strip() == ""
