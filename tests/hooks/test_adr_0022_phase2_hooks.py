"""ADR-0022 Phase 2: Per-agent enforcement scripts + tests.
Steps 2a-2b. Tests T-0022-060 through T-0022-098."""

import json
import subprocess

import pytest

from conftest import (
    ALL_HOOK_SCRIPT_NAMES,
    CLAUDE_DIR,
    PROJECT_ROOT,
    SIMPLIFIED_CONFIG,
    build_per_agent_input,
    hide_jq_env,
    prepare_per_agent_hook,
    run_per_agent_hook,
)


# ═══ Step 2a: Per-Agent Enforcement Scripts ══════════════════════════


def test_T_0022_060_cal_allows_architecture(simplified_env):
    r = run_per_agent_hook("enforce-cal-paths.sh", build_per_agent_input("Write", "docs/architecture/ADR-0022-test.md"), simplified_env)
    assert r.returncode == 0


def test_T_0022_061_cal_blocks_src(simplified_env):
    r = run_per_agent_hook("enforce-cal-paths.sh", build_per_agent_input("Write", "src/main.ts"), simplified_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_T_0022_062_cal_blocks_product(simplified_env):
    r = run_per_agent_hook("enforce-cal-paths.sh", build_per_agent_input("Write", "docs/product/spec.md"), simplified_env)
    assert r.returncode == 2


def test_T_0022_063_roz_allows_tests(simplified_env):
    r = run_per_agent_hook("enforce-roz-paths.sh", build_per_agent_input("Write", "tests/hooks/new-test.bats"), simplified_env)
    assert r.returncode == 0


def test_T_0022_064_roz_allows_pipeline(simplified_env):
    r = run_per_agent_hook("enforce-roz-paths.sh", build_per_agent_input("Write", "docs/pipeline/last-qa-report.md"), simplified_env)
    assert r.returncode == 0


def test_T_0022_065_roz_blocks_src(simplified_env):
    r = run_per_agent_hook("enforce-roz-paths.sh", build_per_agent_input("Write", "src/main.ts"), simplified_env)
    assert r.returncode == 2


def test_T_0022_066_colby_allows_src(simplified_env):
    r = run_per_agent_hook("enforce-colby-paths.sh", build_per_agent_input("Write", "src/features/auth/login.ts"), simplified_env)
    assert r.returncode == 0


def test_T_0022_067_colby_blocks_docs(simplified_env):
    r = run_per_agent_hook("enforce-colby-paths.sh", build_per_agent_input("Write", "docs/guide/user-guide.md"), simplified_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_T_0022_068_colby_blocks_github(simplified_env):
    r = run_per_agent_hook("enforce-colby-paths.sh", build_per_agent_input("Write", ".github/workflows/ci.yml"), simplified_env)
    assert r.returncode == 2


def test_T_0022_069_agatha_allows_docs(simplified_env):
    r = run_per_agent_hook("enforce-agatha-paths.sh", build_per_agent_input("Write", "docs/guide/technical-reference.md"), simplified_env)
    assert r.returncode == 0


def test_T_0022_070_agatha_blocks_src(simplified_env):
    r = run_per_agent_hook("enforce-agatha-paths.sh", build_per_agent_input("Write", "src/main.ts"), simplified_env)
    assert r.returncode == 2


def test_T_0022_071_product_allows_product(simplified_env):
    r = run_per_agent_hook("enforce-product-paths.sh", build_per_agent_input("Write", "docs/product/feature-spec.md"), simplified_env)
    assert r.returncode == 0


def test_T_0022_072_product_blocks_ux(simplified_env):
    r = run_per_agent_hook("enforce-product-paths.sh", build_per_agent_input("Write", "docs/ux/design.md"), simplified_env)
    assert r.returncode == 2


def test_T_0022_073_product_blocks_src(simplified_env):
    r = run_per_agent_hook("enforce-product-paths.sh", build_per_agent_input("Write", "src/main.ts"), simplified_env)
    assert r.returncode == 2


def test_T_0022_074_ux_allows_ux(simplified_env):
    r = run_per_agent_hook("enforce-ux-paths.sh", build_per_agent_input("Write", "docs/ux/feature-design.md"), simplified_env)
    assert r.returncode == 0


def test_T_0022_075_ux_blocks_product(simplified_env):
    r = run_per_agent_hook("enforce-ux-paths.sh", build_per_agent_input("Write", "docs/product/spec.md"), simplified_env)
    assert r.returncode == 2


def test_T_0022_076_ux_blocks_src(simplified_env):
    r = run_per_agent_hook("enforce-ux-paths.sh", build_per_agent_input("Write", "src/main.ts"), simplified_env)
    assert r.returncode == 2


def test_T_0022_077_eva_allows_pipeline(simplified_env):
    r = run_per_agent_hook("enforce-eva-paths.sh", build_per_agent_input("Write", "docs/pipeline/pipeline-state.md"), simplified_env)
    assert r.returncode == 0


def test_T_0022_078_eva_blocks_product(simplified_env):
    r = run_per_agent_hook("enforce-eva-paths.sh", build_per_agent_input("Write", "docs/product/spec.md"), simplified_env)
    assert r.returncode == 2


def test_T_0022_079_eva_blocks_ux(simplified_env):
    r = run_per_agent_hook("enforce-eva-paths.sh", build_per_agent_input("Write", "docs/ux/design.md"), simplified_env)
    assert r.returncode == 2


@pytest.mark.parametrize("hook_name", ALL_HOOK_SCRIPT_NAMES)
def test_T_0022_080_setup_mode_env(hook_name, simplified_env):
    hook_path = prepare_per_agent_hook(hook_name, simplified_env)
    import os
    env = os.environ.copy()
    env["ATELIER_SETUP_MODE"] = "1"
    env["CLAUDE_PROJECT_DIR"] = str(simplified_env)
    r = subprocess.run(
        ["bash", str(hook_path)],
        input=build_per_agent_input("Write", "src/evil.ts"),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, timeout=30,
    )
    assert r.returncode == 0


@pytest.mark.parametrize("hook_name", ALL_HOOK_SCRIPT_NAMES)
def test_T_0022_081_setup_mode_file(hook_name, simplified_env):
    (simplified_env / "docs" / "pipeline" / ".setup-mode").touch()
    hook_path = prepare_per_agent_hook(hook_name, simplified_env)
    import os
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(simplified_env)
    r = subprocess.run(
        ["bash", str(hook_path)],
        input=build_per_agent_input("Write", "src/evil.ts"),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, timeout=30,
    )
    assert r.returncode == 0


@pytest.mark.parametrize("hook_name", ALL_HOOK_SCRIPT_NAMES)
def test_T_0022_082_empty_file_path(hook_name, simplified_env):
    hook_path = prepare_per_agent_hook(hook_name, simplified_env)
    import os
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(simplified_env)
    for inp in ['{"tool_name":"Write","tool_input":{"file_path":""}}', '{"tool_name":"Write","tool_input":{}}']:
        r = subprocess.run(["bash", str(hook_path)], input=inp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, timeout=30)
        assert r.returncode == 0


def test_T_0022_083_colby_normalizes_absolute(simplified_env):
    r = run_per_agent_hook("enforce-colby-paths.sh", build_per_agent_input("Write", f"{simplified_env}/src/feature.ts"), simplified_env)
    assert r.returncode == 0


def test_T_0022_084_colby_blocks_outside_root(simplified_env):
    r = run_per_agent_hook("enforce-colby-paths.sh", build_per_agent_input("Write", "/etc/passwd"), simplified_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_T_0022_085_roz_test_patterns(simplified_env):
    config = {"pipeline_state_dir": "docs/pipeline", "test_patterns": [".custom-test."], "colby_blocked_paths": [], "test_command": ""}
    (simplified_env / "enforcement-config.json").write_text(json.dumps(config))
    r = run_per_agent_hook("enforce-roz-paths.sh", build_per_agent_input("Write", "src/auth.custom-test.ts"), simplified_env)
    assert r.returncode == 0
    r = run_per_agent_hook("enforce-roz-paths.sh", build_per_agent_input("Write", "src/auth.test.ts"), simplified_env)
    assert r.returncode == 2


def test_T_0022_086_colby_blocked_paths(simplified_env):
    config = {"pipeline_state_dir": "docs/pipeline", "test_patterns": [], "colby_blocked_paths": ["custom-blocked/"], "test_command": ""}
    (simplified_env / "enforcement-config.json").write_text(json.dumps(config))
    r = run_per_agent_hook("enforce-colby-paths.sh", build_per_agent_input("Write", "custom-blocked/evil.ts"), simplified_env)
    assert r.returncode == 2
    r = run_per_agent_hook("enforce-colby-paths.sh", build_per_agent_input("Write", "docs/readme.md"), simplified_env)
    assert r.returncode == 0


@pytest.mark.parametrize("hook_name", [
    "enforce-cal-paths.sh", "enforce-roz-paths.sh", "enforce-agatha-paths.sh",
    "enforce-product-paths.sh", "enforce-ux-paths.sh", "enforce-eva-paths.sh",
])
def test_T_0022_087_blocked_message_includes_path(hook_name, simplified_env):
    r = run_per_agent_hook(hook_name, build_per_agent_input("Write", "src/main.ts"), simplified_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout
    assert "src/main.ts" in r.stdout


@pytest.mark.parametrize("hook_name", ALL_HOOK_SCRIPT_NAMES)
def test_T_0022_087a_read_exits_0(hook_name, simplified_env):
    r = run_per_agent_hook(hook_name, build_per_agent_input("Read", "src/any/file.ts"), simplified_env)
    assert r.returncode == 0


def test_T_0022_087b_enforcement_config_keys():
    config = json.loads((CLAUDE_DIR / "hooks" / "enforcement-config.json").read_text())
    assert "pipeline_state_dir" in config
    assert "test_patterns" in config
    assert "colby_blocked_paths" in config
    assert "test_command" in config
    assert "architecture_dir" not in config
    assert "product_specs_dir" not in config
    assert "ux_docs_dir" not in config


def test_T_0022_087c_roz_jq_missing(simplified_env):
    env = hide_jq_env(simplified_env)
    env["CLAUDE_PROJECT_DIR"] = str(simplified_env)
    hook_path = prepare_per_agent_hook("enforce-roz-paths.sh", simplified_env)
    r = subprocess.run(
        ["bash", str(hook_path)],
        input=build_per_agent_input("Write", "tests/foo.test.ts"),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, timeout=30,
    )
    assert r.returncode == 2
    assert "jq" in r.stdout or "jq" in r.stderr


def test_T_0022_087d_colby_jq_missing(simplified_env):
    env = hide_jq_env(simplified_env)
    env["CLAUDE_PROJECT_DIR"] = str(simplified_env)
    hook_path = prepare_per_agent_hook("enforce-colby-paths.sh", simplified_env)
    r = subprocess.run(
        ["bash", str(hook_path)],
        input=build_per_agent_input("Write", "src/main.ts"),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, timeout=30,
    )
    assert r.returncode == 2
    assert "jq" in r.stdout or "jq" in r.stderr


def test_T_0022_087e_eva_blocks_architecture(simplified_env):
    r = run_per_agent_hook("enforce-eva-paths.sh", build_per_agent_input("Write", "docs/architecture/ADR-0022.md"), simplified_env)
    assert r.returncode == 2


def test_T_0022_087f_eva_blocks_src(simplified_env):
    r = run_per_agent_hook("enforce-eva-paths.sh", build_per_agent_input("Write", "src/main.ts"), simplified_env)
    assert r.returncode == 2


# ═══ Step 2b: Test Count Verification ════════════════════════════════


def test_T_0022_092_colby_all_14_blocked():
    """All 13 colby_blocked_paths are enforced (.github/ intentionally removed)."""
    blocked = [
        "docs/readme.md", ".gitlab-ci.yml",
        ".circleci/config.yml", "Jenkinsfile", "Dockerfile",
        "docker-compose.yml", ".gitlab/merge_request_templates/default.md",
        "deploy/prod.yml", "infra/main.tf", "terraform/main.tf",
        "pulumi/index.ts", "k8s/deployment.yml", "kubernetes/service.yml",
    ]
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "docs" / "pipeline").mkdir(parents=True)
        (tmp / "enforcement-config.json").write_text(json.dumps(SIMPLIFIED_CONFIG))
        for p in blocked:
            r = run_per_agent_hook("enforce-colby-paths.sh", build_per_agent_input("Write", p), tmp)
            assert r.returncode == 2, f"Expected block for {p}"
            assert "BLOCKED" in r.stdout


def test_T_0022_093_agatha(simplified_env):
    r = run_per_agent_hook("enforce-agatha-paths.sh", build_per_agent_input("Write", "docs/any/path.md"), simplified_env)
    assert r.returncode == 0
    for p in ["src/main.ts", "package.json"]:
        r = run_per_agent_hook("enforce-agatha-paths.sh", build_per_agent_input("Write", p), simplified_env)
        assert r.returncode == 2


def test_T_0022_094_product(simplified_env):
    r = run_per_agent_hook("enforce-product-paths.sh", build_per_agent_input("Write", "docs/product/new-spec.md"), simplified_env)
    assert r.returncode == 0
    r = run_per_agent_hook("enforce-product-paths.sh", build_per_agent_input("Write", "docs/guide/readme.md"), simplified_env)
    assert r.returncode == 2
    r = run_per_agent_hook("enforce-product-paths.sh", build_per_agent_input("Write", "src/index.ts"), simplified_env)
    assert r.returncode == 2


def test_T_0022_095_ux(simplified_env):
    r = run_per_agent_hook("enforce-ux-paths.sh", build_per_agent_input("Write", "docs/ux/new-design.md"), simplified_env)
    assert r.returncode == 0
    r = run_per_agent_hook("enforce-ux-paths.sh", build_per_agent_input("Write", "docs/product/spec.md"), simplified_env)
    assert r.returncode == 2
    r = run_per_agent_hook("enforce-ux-paths.sh", build_per_agent_input("Write", "src/index.ts"), simplified_env)
    assert r.returncode == 2


def test_T_0022_096_eva(simplified_env):
    r = run_per_agent_hook("enforce-eva-paths.sh", build_per_agent_input("Write", "docs/pipeline/context-brief.md"), simplified_env)
    assert r.returncode == 0
    r = run_per_agent_hook("enforce-eva-paths.sh", build_per_agent_input("Write", "docs/product/spec.md"), simplified_env)
    assert r.returncode == 2
    r = run_per_agent_hook("enforce-eva-paths.sh", build_per_agent_input("Write", "docs/ux/design.md"), simplified_env)
    assert r.returncode == 2


# Import needed for T_0022_092
from pathlib import Path
