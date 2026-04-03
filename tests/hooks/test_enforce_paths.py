"""Tests for enforce-paths.sh (PreToolUse hook). Covers T-0003-014 through T-0003-029."""

import json

from conftest import build_tool_input, hide_jq_env, run_hook


def test_T_0003_014_cal_writing_docs_architecture(hook_env):
    inp = build_tool_input("Write", "docs/architecture/foo.md", "cal")
    r = run_hook("enforce-paths.sh", inp, hook_env)
    assert r.returncode == 0


def test_T_0003_015_cal_writing_src_blocked(hook_env):
    inp = build_tool_input("Write", "src/main.js", "cal")
    r = run_hook("enforce-paths.sh", inp, hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_T_0003_016_absolute_path_not_anchored(hook_env):
    inp = build_tool_input("Write", "/home/user/docs/architecture/evil", "cal")
    r = run_hook("enforce-paths.sh", inp, hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_T_0003_017_colby_writing_src(hook_env):
    inp = build_tool_input("Write", "src/feature.js", "colby")
    r = run_hook("enforce-paths.sh", inp, hook_env)
    assert r.returncode == 0


def test_T_0003_018_colby_writing_docs_blocked(hook_env):
    inp = build_tool_input("Write", "docs/guide/foo.md", "colby")
    r = run_hook("enforce-paths.sh", inp, hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_T_0003_019_jq_missing(hook_env):
    env = hide_jq_env(hook_env)
    inp = build_tool_input("Write", "src/main.js", "colby")
    from conftest import prepare_hook
    import subprocess
    hook_path = prepare_hook("enforce-paths.sh", hook_env)
    r = subprocess.run(["bash", str(hook_path)], input=inp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, timeout=30)
    assert r.returncode == 2
    assert "jq" in r.stdout or "jq" in r.stderr


def test_T_0003_020_roz_writing_test_file(hook_env):
    inp = build_tool_input("Write", "tests/foo.test.js", "roz")
    r = run_hook("enforce-paths.sh", inp, hook_env)
    assert r.returncode == 0


def test_T_0003_021_roz_writing_src_blocked(hook_env):
    inp = build_tool_input("Write", "src/main.js", "roz")
    r = run_hook("enforce-paths.sh", inp, hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_T_0003_022_main_thread_writing_docs_pipeline(hook_env):
    inp = build_tool_input("Write", "docs/pipeline/state.md", "")
    r = run_hook("enforce-paths.sh", inp, hook_env)
    assert r.returncode == 0


def test_T_0003_023_main_thread_writing_src_blocked(hook_env):
    inp = build_tool_input("Write", "src/main.js", "")
    r = run_hook("enforce-paths.sh", inp, hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_T_0003_024_unknown_agent_blocked(hook_env):
    inp = build_tool_input("Write", "anything.txt", "unknown_agent")
    r = run_hook("enforce-paths.sh", inp, hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_T_0003_025_ellis_writing_any_file(hook_env):
    inp = build_tool_input("Write", "src/main.js", "ellis")
    r = run_hook("enforce-paths.sh", inp, hook_env)
    assert r.returncode == 0


def test_T_0003_026_agatha_writing_docs(hook_env):
    inp = build_tool_input("Write", "docs/guide/foo.md", "agatha")
    r = run_hook("enforce-paths.sh", inp, hook_env)
    assert r.returncode == 0


def test_T_0003_027_agatha_writing_src_blocked(hook_env):
    inp = build_tool_input("Write", "src/main.js", "agatha")
    r = run_hook("enforce-paths.sh", inp, hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_T_0003_028_word_splitting_test_patterns(hook_env):
    config = {
        "pipeline_state_dir": "docs/pipeline",
        "architecture_dir": "docs/architecture",
        "product_specs_dir": "docs/product",
        "ux_docs_dir": "docs/ux",
        "colby_blocked_paths": ["docs/"],
        "test_patterns": [".test.", "space pattern", "/tests/"],
        "brain_required_agents": [],
    }
    (hook_env / "enforcement-config.json").write_text(json.dumps(config))

    # File that does NOT match any test pattern -- blocked for roz
    inp = build_tool_input("Write", "src/space.js", "roz")
    r = run_hook("enforce-paths.sh", inp, hook_env)
    assert r.returncode == 2

    # File that matches a normal test pattern -- still works
    inp = build_tool_input("Write", "src/foo.test.js", "roz")
    r = run_hook("enforce-paths.sh", inp, hook_env)
    assert r.returncode == 0


def test_T_0003_029_word_splitting_colby_blocked_paths(hook_env):
    config = {
        "pipeline_state_dir": "docs/pipeline",
        "architecture_dir": "docs/architecture",
        "product_specs_dir": "docs/product",
        "ux_docs_dir": "docs/ux",
        "colby_blocked_paths": ["docs/", "path with spaces/"],
        "test_patterns": [".test."],
        "brain_required_agents": [],
    }
    (hook_env / "enforcement-config.json").write_text(json.dumps(config))

    # Normal source file should NOT be blocked
    inp = build_tool_input("Write", "src/feature.js", "colby")
    r = run_hook("enforce-paths.sh", inp, hook_env)
    assert r.returncode == 0

    # File in docs/ should still be blocked
    inp = build_tool_input("Write", "docs/readme.md", "colby")
    r = run_hook("enforce-paths.sh", inp, hook_env)
    assert r.returncode == 2
