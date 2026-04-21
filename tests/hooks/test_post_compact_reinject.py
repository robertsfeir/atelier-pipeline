"""Tests for ADR-0020 Step 3: PostCompact context preservation hook. Covers T-0020-039 through T-0020-050."""

import json
import subprocess

from conftest import (
    PROJECT_ROOT,
    prepare_hook,
    run_hook_with_project_dir,
    run_hook_without_project_dir,
)


def test_T_0020_039_outputs_pipeline_state(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").write_text(
        "# Pipeline State\n\nFeature: Hook modernization\nPhase: build\n"
    )
    r = run_hook_with_project_dir("post-compact-reinject.sh", "", hook_env)
    assert r.returncode == 0
    assert "Pipeline State" in r.stdout
    assert "Hook modernization" in r.stdout


def test_T_0020_040_outputs_context_brief(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").write_text("# Pipeline State\n\nFeature: Hook modernization\n")
    (hook_env / "docs" / "pipeline" / "context-brief.md").write_text("# Context Brief\n\nWave 2 hook modernization is in progress.\n")
    r = run_hook_with_project_dir("post-compact-reinject.sh", "", hook_env)
    assert r.returncode == 0
    assert "Pipeline State" in r.stdout
    assert "Context Brief" in r.stdout
    assert "Wave 2 hook modernization" in r.stdout


def test_T_0020_041_header_marker(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").write_text("# Pipeline State\n")
    r = run_hook_with_project_dir("post-compact-reinject.sh", "", hook_env)
    assert r.returncode == 0
    first_line = r.stdout.splitlines()[0]
    assert first_line == "--- Re-injected after compaction ---"


def test_T_0020_042_missing_state_file(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").unlink(missing_ok=True)
    r = run_hook_with_project_dir("post-compact-reinject.sh", "", hook_env)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_T_0020_043_unreadable_state_file(hook_env):
    sf = hook_env / "docs" / "pipeline" / "pipeline-state.md"
    sf.write_text("# Pipeline State\n")
    sf.chmod(0o000)
    r = run_hook_with_project_dir("post-compact-reinject.sh", "", hook_env)
    assert r.returncode == 0
    sf.chmod(0o644)


def test_T_0020_044_unset_project_dir(hook_env):
    r = run_hook_without_project_dir("post-compact-reinject.sh", "", hook_env)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_T_0020_045_empty_files(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").write_text("")
    (hook_env / "docs" / "pipeline" / "context-brief.md").write_text("")
    r = run_hook_with_project_dir("post-compact-reinject.sh", "", hook_env)
    assert r.returncode == 0
    assert "Re-injected after compaction" in r.stdout


def test_T_0020_046_only_pipeline_state(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").write_text("# Pipeline State\n\nFeature: Hook modernization\n")
    (hook_env / "docs" / "pipeline" / "context-brief.md").unlink(missing_ok=True)
    r = run_hook_with_project_dir("post-compact-reinject.sh", "", hook_env)
    assert r.returncode == 0
    assert "Pipeline State" in r.stdout
    assert "Hook modernization" in r.stdout


def test_T_0020_047_file_path_labels(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").write_text("# Pipeline State\n")
    (hook_env / "docs" / "pipeline" / "context-brief.md").write_text("# Context Brief\n")
    r = run_hook_with_project_dir("post-compact-reinject.sh", "", hook_env)
    assert r.returncode == 0
    # After ADR-0035, path labels use the resolved $STATE_FILE/$BRIEF_FILE variables
    # instead of hardcoded docs/pipeline/ paths. With CLAUDE_PROJECT_DIR set to
    # hook_env (tmp_path), the fallback resolves to <tmp_path>/docs/pipeline/.
    assert "## From:" in r.stdout
    assert "pipeline-state.md" in r.stdout
    assert "context-brief.md" in r.stdout


def test_T_0020_048_settings_json_post_compact():
    settings = json.loads((PROJECT_ROOT / ".claude" / "settings.json").read_text())
    pc_matchers = settings["hooks"].get("PostCompact", [])
    commands = [h.get("command", "") for m in pc_matchers for h in m.get("hooks", [])]
    assert any("post-compact-reinject.sh" in c for c in commands)


def test_T_0020_049_pre_compact_independent(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").write_text("# Pipeline State\n\nFeature: Hook modernization\n")
    prepare_hook("pre-compact.sh", hook_env)
    import os
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(hook_env)
    r = subprocess.run(
        ["bash", str(hook_env / "pre-compact.sh")],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, timeout=30,
    )
    assert r.returncode == 0
    assert "COMPACTION:" in (hook_env / "docs" / "pipeline" / "pipeline-state.md").read_text()


def test_T_0020_050_security_no_error_patterns(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").write_text("UNIQUE_PIPELINE_STATE_MARKER_50\n")
    (hook_env / "docs" / "pipeline" / "context-brief.md").write_text("UNIQUE_CONTEXT_BRIEF_MARKER_50\n")
    (hook_env / "docs" / "pipeline" / "error-patterns.md").write_text("UNIQUE_ERROR_PATTERNS_MARKER_50\n")
    (hook_env / "docs" / "pipeline" / "investigation-ledger.md").write_text("UNIQUE_INVESTIGATION_LEDGER_MARKER_50\n")
    (hook_env / "docs" / "pipeline" / "last-qa-report.md").write_text("UNIQUE_QA_REPORT_MARKER_50\n")
    r = run_hook_with_project_dir("post-compact-reinject.sh", "", hook_env)
    assert r.returncode == 0
    assert "UNIQUE_PIPELINE_STATE_MARKER_50" in r.stdout
    assert "UNIQUE_CONTEXT_BRIEF_MARKER_50" in r.stdout
    assert "UNIQUE_ERROR_PATTERNS_MARKER_50" not in r.stdout
    assert "UNIQUE_INVESTIGATION_LEDGER_MARKER_50" not in r.stdout


# ═══════════════════════════════════════════════════════════════════════
# ADR-0033 Step 5 (m3): Brain Protocol Reminder wording and scope
# ═══════════════════════════════════════════════════════════════════════

